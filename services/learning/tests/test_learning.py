import json
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from igot_learning.adapters.database import Base, get_db
from igot_learning.api import routes
from igot_learning.application.auth import Principal, admin, internal_secret, optional_principal, principal
from igot_learning.domain.models import (
    Certificate,
    Course,
    Enrollment,
    LearnerProjection,
    Lesson,
    Module,
    ProcessedEvent,
)
from igot_learning.main import app


def _client() -> tuple[TestClient, Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    ).execution_options(schema_translate_map={"learning": None})
    Base.metadata.create_all(engine)
    session = Session(engine, expire_on_commit=False)

    def test_db():
        yield session

    learner = Principal(user_id=7, role="learner")
    administrator = Principal(user_id=1, role="admin")
    app.dependency_overrides[get_db] = test_db
    app.dependency_overrides[principal] = lambda: learner
    app.dependency_overrides[optional_principal] = lambda: learner
    app.dependency_overrides[admin] = lambda: administrator
    app.dependency_overrides[internal_secret] = lambda: None
    return TestClient(app), session


def _seed_course(session: Session) -> Course:
    course = Course(
        id=11,
        title="Official Statistics",
        overview="Learn reproducible official statistics.",
        instructor="NSSTA Faculty",
        organization="MoSPI",
        duration_hours=3,
        difficulty="beginner",
        category="Statistical",
        source="internal",
        is_popular=True,
        assessment_id=91,
    )
    module = Module(id=21, title="Foundations", position=1)
    module.lessons.append(
        Lesson(
            id=31,
            title="Evidence",
            content_type="reading",
            content="# Evidence",
            position=1,
            activity_question="Which source is authoritative?",
            activity_options_json=json.dumps(["Rumour", "Published series"]),
            activity_correct_option=1,
            activity_explanation="Use the published official series.",
        )
    )
    course.modules.append(module)
    session.add(course)
    session.add(
        LearnerProjection(
            user_id=7,
            email="learner@example.gov.in",
            full_name="Test Learner",
            role="learner",
            designation="Statistical Officer",
            department="MoSPI",
        )
    )
    session.commit()
    return course


def test_discover_enroll_player_progress_and_dashboard():
    client, session = _client()
    try:
        _seed_course(session)

        discovered = client.get("/v1/discover/courses?q=Official").json()
        assert discovered["total_results"] == 1
        assert discovered["courses"][0]["modules_count"] == 1
        assert discovered["courses"][0]["has_assessment"] is True

        enrolled = client.post("/v1/courses/11/enroll")
        assert enrolled.status_code == 200
        assert enrolled.json()["first_lesson_id"] == 31

        player = client.get("/v1/learning/course/11/player?lesson_id=31").json()
        assert player["current_lesson"]["activity"]["options"] == ["Rumour", "Published series"]

        activity = client.post("/v1/learning/lesson/31/activity", json={"selected_option": 1})
        assert activity.json()["is_correct"] is True
        completed = client.post("/v1/learning/lesson/31/complete")
        assert completed.json()["progress_percent"] == 100

        dashboard = client.get("/v1/dashboard/summary").json()
        assert dashboard["learner"]["full_name"] == "Test Learner"
        assert dashboard["my_learning_progress"]["in_progress_count"] == 1
    finally:
        app.dependency_overrides.clear()
        session.close()


def test_assessment_completion_event_is_idempotent_and_issues_certificate():
    client, session = _client()
    try:
        _seed_course(session)
        event = {
            "event_id": "evt-1",
            "user_id": 7,
            "course_id": 11,
            "attempt_id": "attempt-1",
            "score_percent": 86.0,
            "passed": True,
            "occurred_at": datetime.now(timezone.utc).isoformat(),
        }
        first = client.post("/v1/internal/events/assessment-completed", json=event)
        second = client.post("/v1/internal/events/assessment-completed", json=event)
        assert first.json()["status"] == "accepted"
        assert second.json()["status"] == "duplicate"
        assert session.scalar(select(func.count(Certificate.id))) == 1
        assert session.scalar(select(func.count(ProcessedEvent.event_id))) == 1
        enrollment = session.scalar(
            select(Enrollment).where(Enrollment.user_id == 7, Enrollment.course_id == 11)
        )
        assert enrollment is not None
        assert enrollment.status == "completed"
    finally:
        app.dependency_overrides.clear()
        session.close()
