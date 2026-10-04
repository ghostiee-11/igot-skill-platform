from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.statistical_engine.core.exceptions import (
    StatisticalEngineException,
    CompetencyNotFoundException,
    AttemptNotFoundException
)
from app.statistical_engine.schemas.stats import CalculationRequest, CalculationResult
from app.statistical_engine.schemas.charts import ChartGenerateRequest, ChartSpec
from app.statistical_engine.schemas.competencies import CompetencySchema, LearnerSkillMasterySchema
from app.statistical_engine.schemas.questions import (
    QuestionInstance,
    QuestionGenerateRequest,
    NextQuestionRequest,
    SubmitAnswerRequest,
    AnswerSubmissionResponse
)
from app.statistical_engine.stats.price_statistics import price_stats_module
from app.statistical_engine.charts.generator import chart_generator
from app.statistical_engine.competency.graph import competency_graph
from app.statistical_engine.repositories.sql_repositories import SQLLearnerRepository
from app.statistical_engine.services.assessment_service import assessment_service

router = APIRouter(tags=["Statistical Competency Engine"])

@router.get("/stats-engine/health")
def engine_health():
    """Service health check endpoint."""
    return {
        "status": "healthy",
        "service": "Statistical Competency Engine",
        "domain_active": "price_statistics",
        "version": "v1"
    }

@router.post("/stats/calculate", response_model=CalculationResult)
def calculate_statistic(req: CalculationRequest):
    """
    Execute a deterministic statistical computation with strict mathematical validation.
    """
    try:
        return price_stats_module.calculate(operation=req.operation, inputs=req.inputs)
    except StatisticalEngineException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": e.code, "message": e.message, "details": e.details}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "CALCULATION_ERROR", "message": str(e)}
        )

@router.post("/questions/generate", response_model=QuestionInstance)
def generate_question_instance(req: QuestionGenerateRequest, db: Session = Depends(get_db)):
    """
    Generate a standalone parameterized question instance with answer key withheld.
    """
    try:
        return assessment_service.generate_question(
            db,
            skill_id=req.skill_id,
            difficulty=req.difficulty,
            question_type=req.question_type,
            seed=req.seed
        )
    except StatisticalEngineException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": e.code, "message": e.message, "details": e.details}
        )

@router.post("/questions/next", response_model=QuestionInstance)
def get_next_adaptive_question(req: NextQuestionRequest, db: Session = Depends(get_db)):
    """
    Select and generate the next personalized question based on learner mastery and context.
    """
    try:
        return assessment_service.get_next_question(
            db,
            user_id=req.user_id,
            competency_id=req.competency_id,
            preferred_skill_id=req.preferred_skill_id,
            current_difficulty=req.current_difficulty,
            question_type=req.question_type,
        )
    except StatisticalEngineException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": e.code, "message": e.message, "details": e.details}
        )

@router.post("/questions/submit", response_model=AnswerSubmissionResponse)
def submit_question_answer(req: SubmitAnswerRequest, db: Session = Depends(get_db)):
    """
    Server-side deterministic answer evaluation, scoring, mastery update, and branching.
    """
    try:
        res = assessment_service.submit_answer(
            db,
            user_id=req.user_id,
            question_id=req.question_id,
            submitted_answer=req.submitted_answer,
            time_taken_seconds=req.time_taken_seconds
        )
        try:
            from app.agents.competency.knowledge_tracing import AttentiveKnowledgeTracingEngine
            uid = int(req.user_id) if str(req.user_id).isdigit() else 2
            AttentiveKnowledgeTracingEngine.compute_mastery_and_gaps(db, uid)
            AttentiveKnowledgeTracingEngine.generate_intelligent_recommendations(db, uid)
        except Exception:
            pass
        return res
    except AttemptNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": e.code, "message": e.message, "details": e.details}
        )
    except StatisticalEngineException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": e.code, "message": e.message, "details": e.details}
        )

@router.post("/charts/generate", response_model=ChartSpec)
def generate_chart_specification(req: ChartGenerateRequest):
    """
    Generate a structured, frontend-agnostic chart specification from a dataset.
    """
    try:
        return chart_generator.create_spec(
            chart_type=req.type,
            title=req.title,
            description=req.description,
            x_field=req.xAxis.field,
            x_label=req.xAxis.label,
            y_field=req.yAxis.field,
            y_label=req.yAxis.label,
            data=req.data,
            unit=req.unit
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "CHART_GENERATION_FAILED", "message": str(e)}
        )

@router.get("/competencies", response_model=List[CompetencySchema])
def list_competencies():
    """
    Retrieve all statistical competency domains and their atomic skills.
    """
    return competency_graph.list_competencies()

@router.get("/competencies/{competency_id}", response_model=CompetencySchema)
def get_competency_details(competency_id: str):
    """
    Retrieve full skill hierarchy and prerequisites for a specific competency domain.
    """
    try:
        return competency_graph.get_competency(competency_id)
    except CompetencyNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": e.code, "message": e.message, "details": e.details}
        )

@router.get("/users/{user_id}/competencies", response_model=Dict[str, Dict[str, Any]])
def get_user_competencies(user_id: str, db: Session = Depends(get_db)):
    """
    Retrieve learner mastery records across all statistical skills.
    """
    return SQLLearnerRepository(db).get_user_mastery(user_id)
