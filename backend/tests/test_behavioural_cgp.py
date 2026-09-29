import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.seed_data import seed_database
from app.core.seed_competencies import seed_competency_taxonomy
from app.main import app
from app.modules.behavioural_cgp.services.corpus import get_all_documents, get_document_by_id
from app.modules.behavioural_cgp.services.carryforward_generator import (
    get_all_cases,
    get_case_by_id,
    generate_case_from_document
)
from app.modules.behavioural_cgp.services.carryforward_session import CarryforwardSessionManager
from app.modules.behavioural_cgp.services.interview_service import InterviewSessionManager
from app.modules.behavioural_cgp.schemas import CaseGenerationRequest, InterviewStartRequest


@pytest.fixture(name="db_session")
def fixture_db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        # These tests exercise course-backed endpoints (courses, case-course mappings,
        # course-anchored generation), so the isolated in-memory DB needs the same seed
        # data the real app loads on startup.
        seed_database(db)
        seed_competency_taxonomy(db)
        yield db
    finally:
        db.close()


@pytest.fixture(name="client")
def fixture_client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

def test_corpus_retrieval():
    docs = get_all_documents()
    assert len(docs) >= 4
    cases = get_all_cases()
    assert len(cases) >= 4
    assert get_case_by_id("case_mospi_nqaf_audit") is not None
    doc_ids = [d.id for d in docs]
    assert "doc_dopt_rule14_proceeding" in doc_ids
    assert "doc_gfr_gem_procurement_notice" in doc_ids
    assert "doc_rti_first_appeal_proceeding" in doc_ids
    assert "doc_mospi_nqaf_audit_notice" in doc_ids

    doc = get_document_by_id("doc_dopt_rule14_proceeding")
    assert doc is not None
    assert "CCS (CCA) Rules" in doc.statutory_reference
    assert len(doc.key_stakeholders) > 0

def test_api_corpus_endpoints(client):
    response = client.get("/api/behavioural/corpus")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 4

    single_res = client.get("/api/behavioural/corpus/doc_gfr_gem_procurement_notice")
    assert single_res.status_code == 200
    assert "GFR Rule 149" in single_res.json()["title"]

def test_dynamic_case_generation_from_notice():
    raw_notice = """
    GOVERNMENT OF INDIA, MINISTRY OF PERSONNEL
    OFFICE MEMORANDUM F.No. 42/2026-Estt
    Subject: Non-compliance with Rule 16 Minor Penalty Timelines
    It has come to notice that several Disciplinary Authorities are failing to issue Form 11 within 15 days
    of receipt of explanation, causing statutory appeals under Rule 23 of CCS Rules.
    All officers are directed to ensure strict adherence to timelines and natural justice.
    """
    req = CaseGenerationRequest(
        raw_text=raw_notice,
        document_title="O.M. on Rule 16 Minor Penalty Adherence",
        document_type="Notice",
        issuing_authority="Department of Personnel & Training",
        statutory_reference="CCS (CCA) Rules, 1965 — Rule 16"
    )
    case = generate_case_from_document(req)
    assert case is not None
    assert case.root_question_id in case.questions
    assert len(case.questions) >= 2
    root_q = case.questions[case.root_question_id]
    assert len(root_q.options) >= 2

def test_carryforward_branching_workflow():
    # Start session with CCS Rule 14 case
    session = CarryforwardSessionManager.create_session(case_id="case_ccs_rule14_inquiry")
    assert session.current_case is not None
    assert session.current_case.id == "case_ccs_rule14_inquiry"
    
    root_q = session.current_question
    assert root_q.id == "q_ccs_root"
    assert root_q.stage_type == "root"

    # Step 1: Officer selects Option B (sub-optimal procedural error: accepts uncertified printouts)
    # This MUST trigger a carryforward branch to q_ccs_branch_bias!
    res_step1 = session.submit_answer(question_id="q_ccs_root", selected_option_id="B")
    assert res_step1.is_optimal is False
    assert res_step1.is_satisfactory_terminal is False
    assert res_step1.carryforward_active is True
    assert res_step1.scenario_completed is False
    assert res_step1.next_question is not None
    assert res_step1.next_question.id == "q_ccs_branch_bias"
    assert res_step1.next_question.stage_type == "carryforward_branch"
    assert "bias" in res_step1.next_question.prompt.lower()

    # Step 2: Officer answers the follow-up carryforward branch question with Option A (remediation)
    # This correctly stays proceedings and resolves the scenario satisfactorily!
    res_step2 = session.submit_answer(question_id="q_ccs_branch_bias", selected_option_id="A")
    assert res_step2.is_optimal is True
    assert res_step2.is_satisfactory_terminal is True
    assert res_step2.scenario_completed is True

    # Check session summary
    summary = session.get_summary()
    assert summary.total_steps == 2
    assert summary.optimal_steps == 1
    assert summary.procedural_compliance_score == 50.0
    assert summary.resolved_satisfactorily is True
    assert len(summary.decision_trail) == 2
    assert "Decision Making" in summary.competency_scores
    assert len(summary.strengths) > 0
    assert len(summary.recommended_upskilling) > 0

def test_api_carryforward_session_endpoints(client):
    # Start via API
    start_res = client.post("/api/behavioural/session/start", json={"case_id": "case_gfr_gem_procurement"})
    assert start_res.status_code == 200
    start_data = start_res.json()
    session_id = start_data["session_id"]
    assert session_id is not None
    assert start_data["case_id"] == "case_gfr_gem_procurement"

    # Submit optimal answer directly (Option A)
    submit_res = client.post(
        f"/api/behavioural/session/{session_id}/submit",
        json={"question_id": "q_gem_root", "selected_option_id": "A"}
    )
    assert submit_res.status_code == 200
    submit_data = submit_res.json()
    assert submit_data["is_optimal"] is True
    assert submit_data["is_satisfactory_terminal"] is True
    assert submit_data["scenario_completed"] is True

    # Get summary
    sum_res = client.get(f"/api/behavioural/session/{session_id}/summary")
    assert sum_res.status_code == 200
    sum_data = sum_res.json()
    assert sum_data["procedural_compliance_score"] == 100.0

def test_live_interview_session_and_analysis():
    # Start interview for Course 1 (Civil Service Ethics)
    req = InterviewStartRequest(course_id=1, officer_name="Sharma", target_duration_minutes=30)
    session = InterviewSessionManager.start_interview(req)
    assert session.session_id is not None
    assert session.course_info["title"] == "Civil Service Conduct, Administrative Ethics & Interpersonal Leadership"
    assert len(session.transcript) == 1

    # Turn 1: Officer answers
    turn1 = session.process_turn(
        officer_text="Hamlet-group formation is mandatory under NSS standards when village population exceeds 1,200 persons or 300 households. Substituting without prior authorization compromises probability proportional to size sampling and violates UN-NQAF methodology.",
        elapsed_seconds=320
    )
    assert turn1.turn_number == 2
    assert "Ethics" in turn1.pacing_advice or "Phase" in turn1.phase_name
    assert turn1.turns_completed == 1

    # Turn 2: Project Management
    turn2 = session.process_turn(
        officer_text="I would allocate contingency budgets, revise regional milestone schedules under our project management framework, and maintain real-time monitoring via digital CAPI dashboards.",
        elapsed_seconds=780
    )
    assert turn2.turns_completed == 2

    # Turn 3: Leadership
    turn3 = session.process_turn(
        officer_text="As team leader, I will accompany junior investigators to the field, engage directly with village representatives, and uphold staff safety while ensuring unbiased survey listing.",
        elapsed_seconds=1250
    )
    assert turn3.turns_completed == 3

    # Turn 4: Ethics
    turn4 = session.process_turn(
        officer_text="Under the Civil Services Conduct Rules and the Collection of Statistics Act, I must maintain absolute impartiality and refuse any unauthorized alteration of official statistical findings.",
        elapsed_seconds=1600
    )
    assert turn4.turns_completed == 4

    # Generate analysis
    analysis = session.generate_analysis()
    assert analysis.officer_name == "Sharma"
    assert analysis.overall_score_percent >= 70.0
    assert len(analysis.competency_scores) == 7
    
    # Check all 6 requested behavioral competencies + Course Knowledge
    for comp in ["Course Knowledge", "Leadership", "Communication", "Project Management", "Ethics", "Decision Making", "Change Management"]:
        assert comp in analysis.competency_scores
        assert analysis.competency_scores[comp].score_percent > 0
        assert analysis.competency_scores[comp].rating_band in ["Exemplary", "Proficient", "Needs Attention"]

    # Verify structured diagnostic report sections
    assert analysis.overall_assessment != ""
    assert analysis.course_understanding != ""
    assert analysis.communication_assessment != ""
    assert analysis.decision_making_assessment != ""
    assert analysis.conversation_analysis != ""
    assert len(analysis.recommended_upskilling) > 0
    assert analysis.video_behavioural_observations.posture_stability_score > 0
    assert analysis.speech_analysis.average_wpm > 0
    assert "Notice:" in analysis.observable_signals_disclaimer

def test_nqaf_carryforward_and_generated_case_session():
    nqaf = get_case_by_id("case_mospi_nqaf_audit")
    assert nqaf is not None
    session = CarryforwardSessionManager.create_session(case_id="case_mospi_nqaf_audit")
    root = session.current_question
    assert root.id == "q_nqaf_root"

    branch_res = session.submit_answer(question_id="q_nqaf_root", selected_option_id="B")
    assert branch_res.carryforward_active is True
    assert branch_res.next_question is not None
    assert branch_res.next_question.id == "q_nqaf_branch_section15"

    close_res = session.submit_answer(question_id="q_nqaf_branch_section15", selected_option_id="A")
    assert close_res.is_satisfactory_terminal is True
    assert close_res.scenario_completed is True

    notice = """
    GOVERNMENT OF INDIA, DEPARTMENT OF PERSONNEL AND TRAINING
    OFFICE MEMORANDUM F.No. 18/2026-Estt
    Subject: Non-compliance with Rule 16 Minor Penalty Timelines
    It has come to notice that several Disciplinary Authorities are failing to issue Form 11 within 15 days
    of receipt of explanation, causing statutory appeals under Rule 23 of CCS Rules.
    All officers are directed to ensure strict adherence to timelines and natural justice.
    """
    generated = generate_case_from_document(CaseGenerationRequest(
        raw_text=notice,
        document_title="O.M. on Rule 16 Minor Penalty Adherence",
        document_type="Notice",
        issuing_authority="DoPT",
        statutory_reference="CCS (CCA) Rules, 1965 — Rule 16"
    ))
    persisted = get_case_by_id(generated.id)
    assert persisted is not None
    custom_session = CarryforwardSessionManager.create_session(case_id=generated.id)
    assert custom_session.current_case is not None
    assert custom_session.current_case.id == generated.id
    gen_res = custom_session.submit_answer(
        question_id=custom_session.current_question.id,
        selected_option_id="B"
    )
    assert gen_res.carryforward_active is True
    assert gen_res.next_question is not None


def test_api_live_interview_flow(client):
    # Start interview API
    res = client.post("/api/behavioural/interview/start", json={
        "course_id": 2,
        "officer_name": "Verma",
        "target_duration_minutes": 28
    })
    assert res.status_code == 200
    data = res.json()
    session_id = data["session_id"]
    assert "Inflation" in data["course_title"]

    # Submit turn API with multimodal telemetry (WPM, eye contact, composure, clarity)
    turn_res = client.post("/api/behavioural/interview/turn", json={
        "session_id": session_id,
        "officer_response": "Jevons Geometric Mean minimizes substitution bias across elementary price quotations according to MoSPI Laspeyres standards under statutory rules.",
        "elapsed_seconds": 250,
        "speaking_pace_wpm": 132.5,
        "eye_contact_percent": 88.0,
        "composure_score": 90.0,
        "voice_clarity_score": 94.0
    })
    assert turn_res.status_code == 200
    turn_data = turn_res.json()
    assert turn_data["turn_number"] == 2
    assert turn_data["target_duration_minutes"] == 28
    assert turn_data["delivery_feedback"] is not None
    assert "132" in turn_data["delivery_feedback"] or "cadence" in turn_data["delivery_feedback"].lower()
    assert len(turn_data["detected_competencies"]) > 0

    # Conclude interview API
    end_res = client.post("/api/behavioural/interview/end", json={"session_id": session_id})
    assert end_res.status_code == 200
    report = end_res.json()
    assert report["overall_rating_band"] is not None
    assert "Ethics" in report["competency_scores"]
    assert "Leadership" in report["competency_scores"]
    assert "Change Management" in report["competency_scores"]
    assert report["telemetry_summary"] is not None
    assert report["telemetry_summary"]["average_speaking_wpm"] > 0
    assert report["telemetry_summary"]["delivery_composure_score"] >= 80.0


def test_get_courses_with_case_mappings(client):
    res = client.get("/api/behavioural/courses")
    assert res.status_code == 200
    courses = res.json()
    assert len(courses) >= 4
    ethics_course = next((c for c in courses if c["course_id"] == 1), None)
    assert ethics_course is not None
    assert "Civil Service Conduct" in ethics_course["title"]
    assert len(ethics_course["mapped_notices"]) > 0
    assert ethics_course["case_count"] >= 1


def test_filter_cases_by_course_id(client):
    # Filter for Course 1 (NSS)
    res_course1 = client.get("/api/behavioural/cases?course_id=1")
    assert res_course1.status_code == 200
    cases_course1 = res_course1.json()
    assert len(cases_course1) >= 1
    for c in cases_course1:
        assert c["course_id"] == 1

    # Route specific for course cases
    res_direct = client.get("/api/behavioural/courses/1/cases")
    assert res_direct.status_code == 200
    cases_direct = res_direct.json()
    assert len(cases_direct) >= 1
    assert cases_direct[0]["course_id"] == 1


def test_generate_course_anchored_case(client):
    # Dynamically generate a new case for Course 4 (Cybersecurity Defense & DPI Governance)
    res = client.post("/api/behavioural/courses/4/generate-case", json={
        "course_id": 4,
        "custom_notice_text": "Ministry of Finance Directive on Treasury Single Account (TSA) fund parking and GeM bidding adherence under GFR 149."
    })
    assert res.status_code == 200
    case_data = res.json()
    assert case_data["course_id"] == 4
    assert "Cybersecurity" in case_data["course_title"] or "Governance" in case_data["course_title"]
    assert "q_root" in case_data["questions"]
    root_q = case_data["questions"]["q_root"]
    assert len(root_q["options"]) >= 2
    # Verify sub-optimal branch leads to carryforward follow-up
    branch_opts = [opt for opt in root_q["options"] if not opt["is_optimal"]]
    assert len(branch_opts) > 0
    assert branch_opts[0]["next_question_id"] in case_data["questions"]


def test_live_interview_with_dynamic_database_course(client):
    # Test starting live interview grounded in Course 4 (Digital Governance & Cybersecurity)
    res_start = client.post("/api/behavioural/interview/start", json={
        "course_id": 4,
        "officer_name": "Sharma",
        "target_duration_minutes": 30
    })
    assert res_start.status_code == 200
    data = res_start.json()
    assert "Cybersecurity" in data["course_title"] or "Governance" in data["course_title"]
    assert "initial_ai_question" in data
    assert len(data["initial_ai_question"]) > 20
    session_id = data["session_id"]

    # Submit turn with telemetry
    turn_res = client.post("/api/behavioural/interview/turn", json={
        "session_id": session_id,
        "officer_response": "We enforce Treasury Single Account protocols strictly to prevent idle parking of scheme funds in commercial banks, mandating Just-in-Time releases under GFR Rule 149.",
        "elapsed_seconds": 180,
        "speaking_pace_wpm": 128.0,
        "eye_contact_percent": 90.0,
        "composure_score": 92.0,
        "voice_clarity_score": 95.0
    })
    assert turn_res.status_code == 200
    turn_data = turn_res.json()
    assert turn_data["turn_number"] == 2
    assert "128" in turn_data["delivery_feedback"] or "cadence" in turn_data["delivery_feedback"].lower()
    assert "Project Management" in turn_data["detected_competencies"] or "Ethics" in turn_data["detected_competencies"]

    # Conclude interview and verify diagnostic analysis
    end_res = client.post(f"/api/behavioural/interview/{session_id}/end")
    assert end_res.status_code == 200
    analysis = end_res.json()
    assert analysis["session_id"] == session_id
    assert analysis["overall_score_percent"] > 70
    assert len(analysis["competency_scores"]) == 7
    assert analysis["telemetry_summary"] is not None
    assert analysis["telemetry_summary"]["average_speaking_wpm"] == 128.0
    assert analysis["telemetry_summary"]["delivery_composure_score"] == 92.0


def test_transcribe_endpoint_flow(client):
    # 1. Test empty audio rejection
    res_empty = client.post("/api/behavioural/interview/transcribe", files={"audio": ("dictation.wav", b"", "audio/wav")})
    assert res_empty.status_code == 400

    # 2. Test valid WAV payload with client speech fallback
    fake_wav = b"RIFF" + b"\x00" * 2000
    res_transcribe = client.post(
        "/api/behavioural/interview/transcribe",
        files={"audio": ("dictation.wav", fake_wav, "audio/wav")},
        data={"client_transcript": "I ensure absolute adherence to CCS Conduct Rule 3 and constitutional integrity."}
    )
    assert res_transcribe.status_code == 200
    data = res_transcribe.json()
    assert "Conduct Rule 3" in data["text"]
    assert "provider" in data



