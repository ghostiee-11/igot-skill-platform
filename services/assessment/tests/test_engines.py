from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from igot_assessment import main
from igot_assessment.database import Base, GeneratedQuiz, GeneratedQuizQuestion, OutboxEvent, get_db
from igot_assessment.engines import REGISTRY, public_state
from igot_assessment.security import Principal, current_principal, require_admin


def _definition() -> dict:
    return {
        "competency_codes": ["C1"],
        "items": [
            {
                "id": "q1",
                "text": "Choose the compliant action",
                "competency_code": "C1",
                "correct_option_index": 0,
                "options": [
                    {"id": "a", "text": "Correct", "compliance_delta": 100},
                    {"id": "b", "text": "Incorrect", "compliance_delta": 0},
                ],
            }
        ],
    }


def test_all_domains_emit_evidence_without_exposing_answer_keys():
    for name in ("statistical", "behavioural", "technical", "digital_governance"):
        engine = REGISTRY[name]
        state = engine.start(_definition())
        assert public_state(state)["current_item"]["options"] == [
            {"id": "a", "text": "Correct"},
            {"id": "b", "text": "Incorrect"},
        ]
        result = engine.finalize(engine.submit(state, {"option_id": "a"}))
        assert result["passed"]
        assert result["evidence"][0]["competency_code"] == "C1"


def _client(monkeypatch) -> tuple[TestClient, Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    ).execution_options(schema_translate_map={"assessment": None})
    Base.metadata.create_all(engine)
    session = Session(engine, expire_on_commit=False)

    def test_db():
        yield session

    learner = Principal(user_id=7, role="learner", full_name="Test Learner")
    administrator = Principal(user_id=1, role="admin", full_name="Administrator")
    main.app.dependency_overrides[get_db] = test_db
    main.app.dependency_overrides[current_principal] = lambda: learner
    main.app.dependency_overrides[require_admin] = lambda: administrator

    async def metadata(_: int) -> dict:
        return {"title": "Official Statistics", "organization": "MoSPI", "duration_hours": 3}

    monkeypatch.setattr(main, "course_metadata", metadata)
    return TestClient(main.app), session


def _assessment_payload() -> dict:
    return {
        "id": 91,
        "course_id": 11,
        "title": "Final assessment",
        "engine": "statistical",
        "time_limit_minutes": 20,
        "pass_threshold_percent": 70,
        "questions": [
            {
                "text": "What is the official answer?",
                "options": ["Correct", "Incorrect"],
                "correct_option_index": 0,
                "explanation": "The first option is correct.",
                "competency_code": "price_statistics",
            }
        ],
    }


def test_assessment_delivery_submission_and_idempotency(monkeypatch):
    client, session = _client(monkeypatch)
    try:
        assert client.post("/v1/assessments", json=_assessment_payload()).status_code == 201
        delivered = client.get("/v1/assessments/91").json()
        assert delivered["questions"][0]["options"] == ["Correct", "Incorrect"]
        assert "correct_option_index" not in delivered["questions"][0]

        headers = {"Idempotency-Key": "submission-1"}
        first = client.post("/v1/assessments/91/submit", json={"answers": {"1": 0}}, headers=headers)
        second = client.post("/v1/assessments/91/submit", json={"answers": {"1": 1}}, headers=headers)
        assert first.status_code == 200
        assert first.json() == second.json()
        assert first.json()["recipient_name"] == "Test Learner"
        assert first.json()["certificate_id"] == "KARM-CERT-11-0007"
        assert session.scalar(select(func.count(OutboxEvent.id))) == 1
    finally:
        main.app.dependency_overrides.clear()
        session.close()


def test_engine_session_uses_stored_assessment_and_finalizes_once(monkeypatch):
    client, session = _client(monkeypatch)
    try:
        client.post("/v1/assessments", json=_assessment_payload())
        started = client.post("/v1/sessions", json={"engine": "statistical", "assessment_id": 91})
        assert started.status_code == 201
        session_id = started.json()["session_id"]
        assert "correct_option_index" not in str(started.json()["state"])

        answered = client.post(
            f"/v1/sessions/{session_id}/submit", json={"answer": {"selected_option": 0}}
        )
        assert answered.status_code == 200
        first = client.post(f"/v1/sessions/{session_id}/finalize")
        second = client.post(f"/v1/sessions/{session_id}/finalize")
        assert first.status_code == 200
        assert first.json() == second.json()
        assert session.scalar(select(func.count(OutboxEvent.id))) == 1
    finally:
        main.app.dependency_overrides.clear()
        session.close()


def test_migrated_quiz_catalogue_delivery_and_submission(monkeypatch):
    client, session = _client(monkeypatch)
    try:
        quiz = GeneratedQuiz(
            id=12, user_id=99, title="Imported quiz", source_name="manual.pdf",
            source_type="pdf", difficulty="intermediate", generator="legacy",
        )
        quiz.questions = [GeneratedQuizQuestion(
            id=21, order=1, question_text="Choose A", options=["A", "B"],
            correct_option_index=0, explanation="A is correct", concept="sampling",
        )]
        session.add(quiz)
        session.commit()

        listing = client.get("/v1/quiz")
        assert listing.status_code == 200
        assert listing.json()[0]["question_count"] == 1
        delivered = client.get("/v1/quiz/12").json()
        assert "correct_index" not in delivered["questions"][0]

        result = client.post("/v1/quiz/12/submit", json={"answers": {"21": 0}})
        assert result.status_code == 200
        assert result.json()["score_percent"] == 100.0
        assert client.get("/v1/quiz/12/attempts").json()[0]["correct_count"] == 1
        assert client.delete("/v1/quiz/12").status_code == 403
    finally:
        main.app.dependency_overrides.clear()
        session.close()
