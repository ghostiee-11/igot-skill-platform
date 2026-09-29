import json
import logging
import re
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import (
    User, TechnicalTranscript, TechnicalLearningObjective, TechnicalLabTemplate,
    TechnicalGeneratedLab, TechnicalLabSolution, TechnicalLabValidationResult
)
from app.modules.technical_courses.schemas import (
    TranscriptIngestRequest, TranscriptProcessResponse,
    ObjectiveExtractionRequest, ObjectiveExtractionResponse,
    DecisionRequest, DecisionResponse,
    LabTemplateSchema, TemplateMatchRequest, TemplateMatchResponse,
    LabGenerationRequest, LabGenerationResponse,
    SolutionGenerationRequest, SolutionGenerationResponse,
    LabValidationResponse, FullPipelineRequest, FullPipelineResponse,
    GeneratedLabSchema, TestCaseSchema, ValidationResultSchema, TestResultItem,
    ExecuteStudentCodeRequest, ExecuteStudentCodeResponse,
    ExecuteCellRequest, ExecuteCellResponse,
    ExportNotebookRequest, ExportNotebookResponse,
    LabAssistantRequest, LabAssistantResponse
)
from app.modules.technical_courses.services.transcript_service import TranscriptService
from app.modules.technical_courses.services.objective_extractor import ObjectiveExtractor
from app.modules.technical_courses.services.decision_service import DecisionService
from app.modules.technical_courses.services.template_service import TemplateService
from app.modules.technical_courses.services.lab_generator import LabGenerator
from app.modules.technical_courses.services.solution_generator import SolutionGenerator
from app.modules.technical_courses.services.sandbox_service import SandboxService
from app.modules.technical_courses.services.pipeline_orchestrator import TechnicalPipelineOrchestrator


router = APIRouter(prefix="/technical-courses", tags=["technical-courses"])
logger = logging.getLogger("technical_courses.lab_assistant")


def _format_db_lab(lab: TechnicalGeneratedLab, db: Session) -> Dict[str, Any]:
    solution = db.query(TechnicalLabSolution).filter(TechnicalLabSolution.lab_id == lab.id).first()
    val_records = db.query(TechnicalLabValidationResult).filter(
        TechnicalLabValidationResult.lab_id == lab.id
    ).order_by(TechnicalLabValidationResult.validated_at.desc()).all()

    test_cases_raw = json.loads(lab.test_cases_json) if lab.test_cases_json else []
    constraints_raw = json.loads(lab.constraints_json) if lab.constraints_json else []

    validation_history = []
    for vr in val_records:
        test_summary = json.loads(vr.test_summary_json) if vr.test_summary_json else []
        validation_history.append({
            "id": vr.id,
            "is_valid": vr.is_valid,
            "sandbox_type": vr.sandbox_type,
            "exit_code": vr.exit_code,
            "execution_time_ms": vr.execution_time_ms,
            "stdout": vr.stdout,
            "stderr": vr.stderr,
            "test_summary": test_summary,
            "error_message": vr.error_message,
            "validated_at": vr.validated_at.isoformat() if vr.validated_at else None
        })

    return {
        "id": lab.id,
        "template_id": lab.template_id,
        "title": lab.title,
        "objective": lab.objective,
        "language": lab.language,
        "difficulty": lab.difficulty,
        "status": lab.status,
        "instructions": lab.instructions,
        "starter_code": lab.starter_code,
        "constraints": constraints_raw,
        "test_cases": test_cases_raw,
        "expected_behavior": lab.expected_behavior,
        "solution": {
            "id": solution.id,
            "reference_code": solution.reference_code,
            "explanation": solution.explanation
        } if solution else None,
        "latest_validation": validation_history[0] if validation_history else None,
        "validation_history": validation_history,
        "created_at": lab.created_at.isoformat() if lab.created_at else None
    }


def _format_template_lab(tmpl, numeric_id: int) -> Dict[str, Any]:
    return {
        "id": numeric_id,
        "template_id": tmpl.id,
        "title": tmpl.title,
        "objective": f"Master {tmpl.skill} in practical public administration data workflows.",
        "language": tmpl.language,
        "difficulty": tmpl.difficulty,
        "status": "validated",
        "instructions": tmpl.instructions_template.format(
            objective=f"Implement and validate {tmpl.title}",
            function_name=tmpl.tags[0] if tmpl.tags else "process_solution"
        ),
        "starter_code": tmpl.starter_code_template,
        "constraints": tmpl.constraints,
        "test_cases": [tc.model_dump() if hasattr(tc, "model_dump") else tc for tc in tmpl.test_cases_template],
        "expected_behavior": "Return structured outputs satisfying test assertions.",
        "solution": {
            "id": 9999,
            "reference_code": tmpl.solution_template,
            "explanation": "Official reference implementation adhering to template test harness."
        },
        "latest_validation": None,
        "validation_history": [],
        "created_at": None
    }


def _resolve_lab_item(lab_identifier: Any, db: Session) -> Dict[str, Any]:
    from app.modules.technical_courses.services.template_service import BUILTIN_LAB_TEMPLATES

    lab_str = str(lab_identifier).strip()

    # 1. Numeric ID lookup
    if lab_str.isdigit():
        num_id = int(lab_str)
        lab = db.query(TechnicalGeneratedLab).filter(TechnicalGeneratedLab.id == num_id).first()
        if lab:
            return _format_db_lab(lab, db)
        if num_id >= 1000:
            tmpl_idx = num_id - 1001
            if 0 <= tmpl_idx < len(BUILTIN_LAB_TEMPLATES):
                return _format_template_lab(BUILTIN_LAB_TEMPLATES[tmpl_idx], num_id)

    # 2. Exact template slug match
    for idx, tmpl in enumerate(BUILTIN_LAB_TEMPLATES):
        if tmpl.id.lower() == lab_str.lower():
            return _format_template_lab(tmpl, 1001 + idx)

    # 3. DB template_id match
    lab_by_tmpl = db.query(TechnicalGeneratedLab).filter(TechnicalGeneratedLab.template_id == lab_str).first()
    if lab_by_tmpl:
        return _format_db_lab(lab_by_tmpl, db)

    # 4. Fuzzy / partial slug match
    clean_slug = lab_str.lower().replace("_", "-")
    for idx, tmpl in enumerate(BUILTIN_LAB_TEMPLATES):
        if clean_slug in tmpl.id.lower() or tmpl.id.lower() in clean_slug:
            return _format_template_lab(tmpl, 1001 + idx)

    raise HTTPException(status_code=404, detail=f"Lab '{lab_str}' not found")


def _lab_assistant_context(lab_id: Any, db: Session) -> Dict[str, Any]:
    resolved = _resolve_lab_item(lab_id, db)
    return {
        "title": resolved["title"],
        "objective": resolved["objective"],
        "instructions": resolved["instructions"],
        "constraints": resolved["constraints"],
        "starter_code": resolved["starter_code"],
    }


def _safe_coaching_fallback(question: str, output: Optional[str]) -> str:
    if output:
        final_line = next((line.strip() for line in reversed(output.splitlines()) if line.strip()), "the latest output")
        return (
            f"Start with the last signal from your run: “{final_line[:180]}”. "
            "Which assumption in your function does that line contradict? Check the function inputs and trace one small example by hand, "
            "then rerun only the active cell. Tell me what value first differs from what you expected."
        )
    if re.search(r"\b(answer|solution|complete code|write it for me)\b", question, re.I):
        return (
            "I won’t provide the completed solution, but I can help you reach it. Identify the required input and output shapes first. "
            "Then describe one transformation the function must perform before it can produce that output. Which transformation are you least sure about?"
        )
    return (
        "Let’s narrow this down without jumping to the solution. What should the function return for the smallest valid input you can invent? "
        "Write that example down, trace your current code against it, and tell me the first step where the actual state differs from your expectation."
    )


def _contains_direct_solution(text: str) -> bool:
    return "```" in text or bool(re.search(r"(?m)^\s*(def |class |for .+:|while .+:|return\s+[{\[])" , text))


# 1. Transcript Ingestion & Processing
@router.post("/process", response_model=TranscriptProcessResponse)
def process_transcript(
    req: TranscriptIngestRequest,
    db: Session = Depends(get_db)
):
    """
    Ingests, cleans, normalizes, and chunks a technical-course transcript.
    """
    try:
        return TranscriptService.process_and_persist(req, db=db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process transcript: {str(e)}")


# 2. Learning Objective Extraction
@router.post("/objectives", response_model=ObjectiveExtractionResponse)
def extract_learning_objectives(
    req: ObjectiveExtractionRequest,
    db: Session = Depends(get_db)
):
    """
    Extracts structured, measurable learning objectives from technical course text.
    """
    try:
        return ObjectiveExtractor.extract_objectives(req, db=db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to extract objectives: {str(e)}")


# 3. Quiz vs Lab Decision Layer
@router.post("/decide-mode", response_model=DecisionResponse)
def decide_assessment_mode(req: DecisionRequest):
    """
    Determines whether a learning objective is best suited for a Hands-on Lab or a Quiz.
    """
    return DecisionService.evaluate(req)


# 4. Lab Templates Catalog
@router.get("/templates", response_model=List[LabTemplateSchema])
def list_lab_templates(db: Session = Depends(get_db)):
    """
    Retrieves human-created lab templates defining structural constraints and test harnesses.
    """
    return TemplateService.get_all_templates(db=db)


# 5. Template Matching
@router.post("/match-template", response_model=TemplateMatchResponse)
def match_template_for_objective(
    req: TemplateMatchRequest,
    db: Session = Depends(get_db)
):
    """
    Matches a learning objective to the most suitable human-created lab template.
    """
    return TemplateService.match_template(req, db=db)


# 6. Lab Generation (Template Filling)
@router.post("/labs/generate", response_model=LabGenerationResponse)
def generate_lab_from_template(
    req: LabGenerationRequest,
    db: Session = Depends(get_db)
):
    """
    Generates a concrete lab by filling a human-created template using structured LLM synthesis.
    """
    try:
        return LabGenerator.generate_lab(req, db=db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Lab generation failed: {str(e)}")


# 7. Reference Solution Generation
@router.post("/labs/{lab_id}/solution", response_model=SolutionGenerationResponse)
def generate_solution_for_lab(
    lab_id: str,
    db: Session = Depends(get_db)
):
    """
    Generates candidate reference solution code for a generated lab or built-in template.
    Note: Code is marked untrusted until sandbox validation passes.
    """
    try:
        resolved = _resolve_lab_item(lab_id, db)
        numeric_id = resolved["id"]
        if numeric_id >= 1000 and resolved.get("solution"):
            return SolutionGenerationResponse(
                solution_id=resolved["solution"]["id"],
                lab_id=numeric_id,
                reference_code=resolved["solution"]["reference_code"],
                explanation=resolved["solution"].get("explanation", "Official reference implementation."),
                is_trusted=True
            )
        return SolutionGenerator.generate_solution(
            SolutionGenerationRequest(lab_id=numeric_id, persist=True),
            db=db
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Solution generation failed: {str(e)}")


# 8. Sandbox Validation
@router.post("/labs/{lab_id}/validate", response_model=LabValidationResponse)
def validate_lab_in_sandbox(
    lab_id: str,
    db: Session = Depends(get_db)
):
    """
    Validates a generated or template lab by executing its reference solution and test harness
    in an isolated Docker sandbox (or isolated subprocess testing fallback).
    """
    try:
        resolved = _resolve_lab_item(lab_id, db)
        numeric_id = resolved["id"]
        if numeric_id >= 1000:
            test_cases = [
                TestCaseSchema(**tc) if isinstance(tc, dict) else tc
                for tc in resolved.get("test_cases", [])
            ]
            val_result = SandboxService.validate_code(
                solution_code=resolved["solution"]["reference_code"] if resolved.get("solution") else "",
                test_cases=test_cases
            )
            return LabValidationResponse(
                lab_id=numeric_id,
                is_valid=val_result.is_valid,
                status="validated" if val_result.is_valid else "rejected",
                validation_details=val_result
            )
        return SandboxService.validate_lab(lab_id=numeric_id, db=db)
    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sandbox validation failed: {str(e)}")


# 9. Get Generated Lab Details
@router.get("/labs/{lab_id}")
def get_lab_details(
    lab_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves full details of a generated or built-in lab by integer ID or string slug,
    including its solution, test cases, and validation history.
    """
    return _resolve_lab_item(lab_id, db)


# 10. End-to-End Pipeline Orchestration
@router.post("/pipeline/run-full", response_model=FullPipelineResponse)
def run_full_technical_pipeline(
    req: FullPipelineRequest,
    db: Session = Depends(get_db)
):
    """
    Convenience endpoint executing the entire technical course pipeline end-to-end:
    Transcript -> Objectives -> Decision -> Template Match -> Lab Gen -> Solution Gen -> Sandbox Validation.
    """
    try:
        return TechnicalPipelineOrchestrator.run_pipeline(req, db=db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {str(e)}")


# 11. List All Available Labs (Catalog & Generated)
@router.get("/labs")
def list_all_labs(
    skill: Optional[str] = None,
    difficulty: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Returns all hands-on labs available in the system, combining database-generated labs
    and built-in catalog templates for immediate interactive learning.
    """
    query = db.query(TechnicalGeneratedLab)
    if difficulty:
        query = query.filter(TechnicalGeneratedLab.difficulty == difficulty)
    db_labs = query.all()

    result = []
    # Add database labs
    for lab in db_labs:
        test_cases_raw = json.loads(lab.test_cases_json) if lab.test_cases_json else []
        constraints_raw = json.loads(lab.constraints_json) if lab.constraints_json else []
        result.append({
            "id": lab.id,
            "template_id": lab.template_id,
            "title": lab.title,
            "objective": lab.objective,
            "language": lab.language,
            "difficulty": lab.difficulty,
            "status": lab.status,
            "instructions": lab.instructions,
            "starter_code": lab.starter_code,
            "constraints": constraints_raw,
            "test_cases_count": len(test_cases_raw),
            "created_at": lab.created_at.isoformat() if lab.created_at else None,
            "is_generated": True
        })

    # Add built-in template catalog labs with negative/virtual IDs if not already present
    from app.modules.technical_courses.services.template_service import BUILTIN_LAB_TEMPLATES
    for idx, tmpl in enumerate(BUILTIN_LAB_TEMPLATES, start=1001):
        if skill and skill.lower() not in tmpl.skill.lower():
            continue
        if difficulty and difficulty.lower() != tmpl.difficulty.lower():
            continue
        result.append({
            "id": idx,
            "template_id": tmpl.id,
            "title": tmpl.title,
            "objective": f"Master {tmpl.skill} in practical public administration data workflows.",
            "language": tmpl.language,
            "difficulty": tmpl.difficulty,
            "status": "validated",
            "instructions": tmpl.instructions_template.format(
                objective=f"Implement and validate {tmpl.title}",
                function_name="process_api_request"
            ),
            "starter_code": tmpl.starter_code_template,
            "constraints": tmpl.constraints,
            "test_cases_count": len(tmpl.test_cases_template),
            "created_at": None,
            "is_generated": False,
            "tags": tmpl.tags
        })

    return result


# 12. Contextual lab coaching assistant
@router.post("/labs/{lab_id}/assistant", response_model=LabAssistantResponse)
def coach_lab_learner(
    lab_id: str,
    req: LabAssistantRequest,
    db: Session = Depends(get_db),
):
    """Give contextual, Socratic help without exposing a completed lab solution."""
    context = _lab_assistant_context(lab_id, db)
    history = "\n".join(f"{item.role}: {item.content}" for item in req.history[-6:]) or "No earlier conversation."
    prompt = f"""
You are the iGOT Karmayogi Lab Guide, a patient technical coach inside an interactive Python lab.

NON-NEGOTIABLE COACHING RULES:
- Never provide completed code, a full function implementation, a final answer, hidden test assertions, or a reference solution.
- Do not output fenced code blocks or copy-paste-ready code.
- Do not claim the learner is correct without evidence from their run output.
- Use a Socratic progression: diagnose the current obstacle, give one conceptual hint, and suggest one small next action.
- If asked for the answer, refuse briefly and redirect to the next reasoning step.
- Keep the response under 140 words. Ask at most one focused question.

LAB TITLE: {context['title']}
OBJECTIVE: {context['objective']}
INSTRUCTIONS: {context['instructions']}
REQUIREMENTS: {json.dumps(context['constraints'])}
STARTER CODE (context only; never complete it):
{context['starter_code']}

LEARNER'S CURRENT NOTEBOOK CODE:
{req.current_code or '(No code entered yet.)'}

LATEST CELL OUTPUT:
{req.active_output or '(No output yet.)'}

RECENT CONVERSATION:
{history}

LEARNER QUESTION: {req.message}
""".strip()

    response = ""
    source = "guided-fallback"
    try:
        from app.agents.recommendation.agent import get_llm_client

        client = get_llm_client()
        if client is not None:
            response = str(client.invoke(prompt).content).strip()
            source = "lab-guide-llm"
    except Exception as exc:
        logger.warning("Lab assistant LLM failed: %s", exc)

    if not response or _contains_direct_solution(response):
        response = _safe_coaching_fallback(req.message, req.active_output)
        source = "guided-fallback"

    return LabAssistantResponse(
        response=response[:1600],
        source=source,
        suggestions=["Explain my latest error", "Give me a smaller hint", "What should I test next?"],
    )


# 13. Execute Student Submission
@router.post("/labs/{lab_id}/execute", response_model=ExecuteStudentCodeResponse)
def execute_student_submission(
    lab_id: str,
    req: ExecuteStudentCodeRequest,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Validates learner code by executing test harness assertions in the isolated Sandbox.
    Supports both integer IDs and human-readable string slugs.
    """
    try:
        resolved = _resolve_lab_item(lab_id, db)
        test_cases = [
            TestCaseSchema(**tc) if isinstance(tc, dict) else tc
            for tc in resolved.get("test_cases", [])
        ]
        val_result = SandboxService.validate_code(
            solution_code=req.code,
            test_cases=test_cases
        )
        all_passed = val_result.is_valid
        feedback = (
            "All test cases passed! Verification badge earned."
            if all_passed else
            f"{val_result.passed_tests_count} of {val_result.total_tests_count} test cases passed. Review failing test cases."
        )

        # Real-time Attentive Knowledge Tracing (AKT) trigger
        try:
            from app.agents.competency.knowledge_tracing import AttentiveKnowledgeTracingEngine
            uid = current_user.id if current_user else 2
            AttentiveKnowledgeTracingEngine.compute_mastery_and_gaps(db, uid)
            AttentiveKnowledgeTracingEngine.generate_intelligent_recommendations(db, uid)
        except Exception:
            pass

        return ExecuteStudentCodeResponse(
            lab_id=resolved["id"],
            all_passed=all_passed,
            passed_tests_count=val_result.passed_tests_count,
            total_tests_count=val_result.total_tests_count,
            test_results=val_result.test_results,
            execution_time_ms=val_result.execution_time_ms,
            stdout=val_result.stdout,
            stderr=val_result.stderr,
            exit_code=val_result.exit_code,
            feedback=feedback
        )
    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lab execution failed: {str(e)}")


# 14. Execute Arbitrary Notebook Cell in Sandbox
@router.post("/sandbox/execute-code", response_model=ExecuteCellResponse)
def execute_notebook_cell(req: ExecuteCellRequest):
    """
    Runs an interactive Python code snippet / notebook cell inside the isolated Docker/Subprocess Sandbox.
    """
    try:
        return SandboxService.execute_cell_code(
            code=req.code,
            context_code=req.context_code or ""
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cell execution failed: {str(e)}")


# 15. Export Notebook (Marimo Reactive App or Jupyter .ipynb)
@router.post("/notebook/export", response_model=ExportNotebookResponse)
def export_notebook(req: ExportNotebookRequest):
    """
    Exports interactive lab cells to standard Jupyter (.ipynb) or Marimo reactive app (.py) format.
    """
    clean_title = req.title.replace(" ", "_").lower()
    
    if req.format.lower() == "marimo":
        filename = f"{clean_title}_marimo.py"
        mime_type = "text/x-python"
        
        # Build pure Python reactive Marimo file
        marimo_lines = [
            "# -*- coding: utf-8 -*-",
            "import marimo",
            "",
            '__generated_with = "0.10.0"',
            'app = marimo.App(width="medium", app_title=' + json.dumps(req.title) + ")",
            "",
            "@app.cell",
            "def __():",
            "    import marimo as mo",
            "    return (mo,)",
            ""
        ]
        
        for idx, cell in enumerate(req.cells, start=1):
            cell_type = cell.get("type", "code")
            content = cell.get("content", "")
            
            marimo_lines.append("@app.cell")
            marimo_lines.append(f"def _cell_{idx}(mo):")
            
            if cell_type == "markdown":
                escaped_md = repr(content)
                marimo_lines.append(f"    _md = mo.md({escaped_md})")
                marimo_lines.append("    return (_md,)")
            else:
                for line in content.splitlines():
                    marimo_lines.append(f"    {line}")
                if not content.strip():
                    marimo_lines.append("    pass")
                marimo_lines.append("    return")
            marimo_lines.append("")
            
        marimo_lines.extend([
            'if __name__ == "__main__":',
            "    app.run()",
            ""
        ])
        
        content_str = "\n".join(marimo_lines)
    else:
        filename = f"{clean_title}_notebook.ipynb"
        mime_type = "application/x-ipynb+json"
        
        # Build standard Jupyter Notebook JSON (nbformat v4)
        ipynb_cells = []
        for cell in req.cells:
            cell_type = cell.get("type", "code")
            content = cell.get("content", "")
            lines = [l + "\n" for l in content.splitlines()]
            if lines and lines[-1].endswith("\n"):
                lines[-1] = lines[-1][:-1]
                
            if cell_type == "markdown":
                ipynb_cells.append({
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": lines
                })
            else:
                ipynb_cells.append({
                    "cell_type": "code",
                    "execution_count": cell.get("execution_count", 1),
                    "metadata": {},
                    "outputs": [],
                    "source": lines
                })
                
        ipynb_data = {
            "cells": ipynb_cells,
            "metadata": {
                "language_info": {
                    "name": "python",
                    "version": "3.11"
                },
                "kernelspec": {
                    "display_name": "Python 3 (iGot Karmayogi Sandbox)",
                    "language": "python",
                    "name": "python3"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 5
        }
        content_str = json.dumps(ipynb_data, indent=2)

    return ExportNotebookResponse(
        filename=filename,
        content=content_str,
        format=req.format.lower(),
        mime_type=mime_type
    )

