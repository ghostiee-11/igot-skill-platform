"""Build a notice-grounded carry-forward decision tree."""

from uuid import uuid4


def build_case(text: str, title: str, document_type: str, authority: str, citation: str,
               course_id: int | None = None, course_title: str = "", course_organization: str = "") -> dict:
    notice = " ".join(text.split())[:5000]
    case_id = f"case-{uuid4()}"
    root = f"q-{uuid4()}"
    recovery = f"q-{uuid4()}"
    return {
        "id": case_id, "title": title, "category": "Notice-based administrative decision making",
        "course_id": course_id, "course_title": course_title, "course_organization": course_organization,
        "document_id": f"document-{uuid4()}", "document_title": title, "document_type": document_type,
        "statutory_citations": [citation] if citation else [],
        "initial_context": f"You are an officer applying {title}, issued by {authority}. Relevant notice text: {notice}",
        "root_question_id": root,
        "questions": {
            root: {"id": root, "case_id": case_id, "stage_type": "root",
                   "prompt": "A colleague proposes acting immediately without checking the notice's requirements or recording the reasons. What should you do?",
                   "context_update": f"The decision is governed by {title}.",
                   "behavioral_competencies": ["decision making", "accountability"],
                   "options": [
                       {"option_id": "A", "text": "Check the notice's applicable conditions, document the evidence and reasons, then act within your authority.", "is_optimal": True, "is_satisfactory_terminal": True, "consequence_summary": "The decision remains traceable to the notice and its evidence.", "statutory_rationale": f"The action is checked against {title} rather than assumed to be authorized.", "next_question_id": None},
                       {"option_id": "B", "text": "Proceed on the colleague's assurance without checking the notice.", "is_optimal": False, "is_satisfactory_terminal": False, "consequence_summary": "The decision is challenged because the applicable requirements were not verified.", "statutory_rationale": f"An unsupported assurance does not establish compliance with {title}.", "next_question_id": recovery},
                   ]},
            recovery: {"id": recovery, "case_id": case_id, "stage_type": "carryforward_branch",
                       "prompt": "The decision has been questioned. How do you repair the process?",
                       "context_update": f"Re-check the original notice: {notice[:700]}",
                       "behavioral_competencies": ["accountability", "problem solving"],
                       "options": [
                           {"option_id": "A", "text": "Pause, verify the applicable clause and evidence, correct the decision if needed, and record the reasons.", "is_optimal": True, "is_satisfactory_terminal": True, "consequence_summary": "The issue is corrected with an auditable record.", "statutory_rationale": f"The review is anchored in {title}.", "next_question_id": None},
                           {"option_id": "B", "text": "Dismiss the objection without reviewing the notice.", "is_optimal": False, "is_satisfactory_terminal": False, "consequence_summary": "The unresolved discrepancy remains open to challenge.", "statutory_rationale": "An unreasoned response does not demonstrate notice compliance.", "next_question_id": None},
                       ]},
        },
        "learning_objectives": [f"Apply the requirements of {title}", "Document a reasoned decision", "Correct an unsupported decision"],
    }
