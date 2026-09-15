from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import Course, User
from app.agents.igot.client import domain_category_filter
from .schemas import (
    GovernmentDocument,
    CaseScenario,
    CourseCaseOverview,
    GenerateCaseForCourseRequest,
    CarryforwardQuestion,
    CarryforwardSessionStartRequest,
    CarryforwardAnswerRequest,
    CarryforwardAnswerResponse,
    CarryforwardSessionSummary,
    CaseGenerationRequest,
    InterviewStartRequest,
    InterviewTurnRequest,
    InterviewTurnResponse,
    InterviewEndRequest,
    InterviewAnalysisResponse
)
from .services.corpus import get_all_documents, get_document_by_id
from .services.carryforward_generator import (
    get_all_cases,
    get_case_by_id,
    get_cases_for_course,
    generate_case_from_document,
    generate_case_for_course,
    COURSE_NOTICE_MAPPING
)
from .services.carryforward_session import CarryforwardSessionManager
from .services.interview_service import InterviewSessionManager
from .services.result_store import save_behavioural_result

router = APIRouter(prefix="/behavioural", tags=["behavioural_cgp"])

# --- Course Curriculum & Case Mappings Endpoints ---

@router.get("/courses", response_model=List[CourseCaseOverview])
def list_courses_with_case_metadata(
    behavioural_only: bool = Query(False, description="Only behavioural and managerial courses"),
    db: Session = Depends(get_db),
):
    """Returns database courses with their mapped statutory notices and case scenario counts."""
    query = db.query(Course)
    if behavioural_only:
        query = query.filter(domain_category_filter("behavioural"))
    courses = query.order_by(Course.id).all()
    result = []
    for c in courses:
        cases = get_cases_for_course(c.id)
        mapped_doc_id = COURSE_NOTICE_MAPPING.get(c.id)
        doc = get_document_by_id(mapped_doc_id) if mapped_doc_id else None
        mapped_notices = [doc.title] if doc else []
        result.append(CourseCaseOverview(
            course_id=c.id,
            title=c.title,
            organization=c.organization,
            category=c.category,
            overview=c.overview,
            mapped_notices=mapped_notices,
            case_count=len(cases)
        ))
    return result

@router.get("/courses/{course_id}/cases", response_model=List[CaseScenario])
def get_course_case_scenarios(course_id: int):
    """Returns all carryforward cases specific to a database course."""
    return get_cases_for_course(course_id)

@router.post("/courses/{course_id}/generate-case", response_model=CaseScenario)
def generate_course_anchored_case(
    course_id: int,
    req: Optional[GenerateCaseForCourseRequest] = None,
    db: Session = Depends(get_db)
):
    """
    Extracts syllabus concepts from the specified database course and synthesizes
    a course-anchored carryforward branching case scenario.
    """
    payload = req or GenerateCaseForCourseRequest(course_id=course_id)
    payload.course_id = course_id
    try:
        case = generate_case_for_course(db, payload)
        return case
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate course case: {e}")

# --- Corpus & Government Documents Endpoints ---

@router.get("/corpus", response_model=List[GovernmentDocument])
def list_government_documents():
    """Returns official repository of government notices, statutory forms, and proceedings."""
    return get_all_documents()

@router.get("/corpus/{doc_id}", response_model=GovernmentDocument)
def get_government_document(doc_id: str):
    doc = get_document_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Government document not found")
    return doc

# --- Carryforward Cases & Generator Endpoints ---

@router.get("/cases", response_model=List[CaseScenario])
def list_case_scenarios(course_id: Optional[int] = Query(default=None, description="Filter cases by course ID")):
    """Returns all pre-seeded and active case scenarios, optionally filtered by database course ID."""
    return get_all_cases(course_id=course_id)

@router.get("/cases/{case_id}", response_model=CaseScenario)
def get_case_scenario(case_id: str):
    case = get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case scenario not found")
    return case

@router.post("/cases/generate", response_model=CaseScenario)
def generate_custom_case(req: CaseGenerationRequest):
    """
    Ingests raw government notice or form text and dynamically generates an authentic
    carryforward branching case scenario.
    """
    if not req.raw_text or len(req.raw_text.strip()) < 50:
        raise HTTPException(status_code=400, detail="Document text must contain at least 50 characters")
    case = generate_case_from_document(req)
    return case

# --- Interactive Carryforward Session Runner Endpoints ---

@router.post("/session/start")
def start_carryforward_session(
    req: Optional[CarryforwardSessionStartRequest] = None,
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Initializes an interactive assessment session for carryforward case MCQs.
    """
    case_id = req.case_id if req else None
    session = CarryforwardSessionManager.create_session(
        case_id=case_id,
        user_id=current_user.id if current_user else None
    )
    
    current_q = session.current_question
    case = session.current_case
    
    return {
        "session_id": session.session_id,
        "case_id": case.id if case else None,
        "case_title": case.title if case else None,
        "document_title": case.document_title if case else None,
        "document_type": case.document_type if case else None,
        "initial_context": case.initial_context if case else None,
        "current_question": current_q
    }

@router.get("/session/{session_id}/current")
def get_current_session_question(session_id: str):
    session = CarryforwardSessionManager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session.session_id,
        "case_id": session.current_case.id if session.current_case else None,
        "case_title": session.current_case.title if session.current_case else None,
        "session_completed": session.session_completed,
        "total_steps": session.total_steps,
        "optimal_steps": session.optimal_steps,
        "current_question": session.current_question
    }

@router.post("/session/{session_id}/submit", response_model=CarryforwardAnswerResponse)
def submit_carryforward_answer(session_id: str, req: CarryforwardAnswerRequest):
    """
    Submits an answer to the current MCQ. If the answer introduces procedural complications
    or regulatory notice consequences, branches into a carryforward follow-up MCQ.
    If answered satisfactorily, concludes the scenario and advances to subsequent cases.
    """
    session = CarryforwardSessionManager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        res = session.submit_answer(
            question_id=req.question_id,
            selected_option_id=req.selected_option_id
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/session/{session_id}/summary", response_model=CarryforwardSessionSummary)
def get_carryforward_session_summary(session_id: str, db: Session = Depends(get_db)):
    session = CarryforwardSessionManager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    summary = session.get_summary()
    if session.session_completed:
        save_behavioural_result(
            db,
            session_id=session.session_id,
            session_type="carryforward",
            user_id=session.user_id,
            case_or_course_id=summary.case_id,
            score=summary.procedural_compliance_score,
            result_payload=summary.model_dump(),
        )
    return summary

# --- AI Live Feed Interview Endpoints ---

@router.post("/interview/start")
def start_live_interview(
    req: InterviewStartRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Initiates a live AI oral competency interview dynamically grounded in the specified course syllabus and notices.
    """
    session = InterviewSessionManager.start_interview(
        req, db=db, user_id=current_user.id if current_user else None
    )
    first_q = session.transcript[0].content
    return {
        "session_id": session.session_id,
        "course_id": session.course_id,
        "course_title": session.course_info["title"],
        "officer_name": session.officer_name,
        "target_duration_minutes": session.target_duration_minutes,
        "initial_ai_question": first_q,
        "current_phase": session.current_phase["name"],
        "primary_competency": session.current_phase["primary"]
    }

@router.post("/interview/turn", response_model=InterviewTurnResponse)
def submit_interview_turn(req: InterviewTurnRequest):
    """
    Submits the officer's verbal/text answer with multimodal delivery telemetry (WPM, eye contact, composure).
    The AI evaluates both course knowledge and the 6 behavioral competencies, generating an adaptive follow-up question.
    """
    session = InterviewSessionManager.get_session(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")
    
    telemetry = req.model_dump(exclude={"session_id", "officer_response", "elapsed_seconds"})
    return session.process_turn(
        officer_text=req.officer_response,
        elapsed_seconds=req.elapsed_seconds,
        telemetry=telemetry,
    )

@router.post("/interview/end", response_model=InterviewAnalysisResponse)
def conclude_interview_by_body(req: InterviewEndRequest, db: Session = Depends(get_db)):
    """Concludes the interview when session_id is supplied in the request body."""
    return conclude_and_analyze_interview(req.session_id, db)


@router.post("/interview/{session_id}/end", response_model=InterviewAnalysisResponse)
def conclude_and_analyze_interview(session_id: str, db: Session = Depends(get_db)):
    """
    Concludes the 25-35 min interview and generates the comprehensive diagnostic scorecard
    evaluating Course Knowledge + 6 Behavioral Competencies.
    """
    session = InterviewSessionManager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")

    analysis = session.generate_analysis()
    save_behavioural_result(
        db,
        session_id=session.session_id,
        session_type="interview",
        user_id=session.user_id,
        case_or_course_id=str(session.course_id),
        score=analysis.overall_score_percent,
        result_payload=analysis.model_dump(),
    )
    return analysis
