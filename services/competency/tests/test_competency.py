from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from igot_competency.adapters.database import Base, get_db
from igot_competency.application.auth import Principal, admin, internal, principal
from igot_competency.domain.models import (
    Competency,
    CourseCandidate,
    Domain,
    Evidence,
    Gap,
    Recommendation,
)
from igot_competency.main import app


def _client() -> tuple[TestClient, Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    ).execution_options(schema_translate_map={"competency": None})
    Base.metadata.create_all(engine)
    session = Session(engine, expire_on_commit=False)

    def test_db():
        yield session

    learner = Principal(user_id=7, role="learner")
    administrator = Principal(user_id=1, role="admin")
    app.dependency_overrides[get_db] = test_db
    app.dependency_overrides[principal] = lambda: learner
    app.dependency_overrides[admin] = lambda: administrator
    app.dependency_overrides[internal] = lambda: None
    return TestClient(app), session


def _seed_taxonomy(session: Session) -> None:
    statistical = Domain(id=1, code="statistical", name="Statistical", description="Methods")
    statistical.competencies.append(
        Competency(id=10, code="price_statistics", name="Price Statistics", max_level=5)
    )
    technical = Domain(id=2, code="technical", name="Technical", description="Tools")
    technical.competencies.append(
        Competency(id=20, code="python", name="Python", max_level=5)
    )
    session.add_all(
        [
            statistical,
            technical,
            CourseCandidate(
                course_id=31,
                title="Price Statistics",
                category="Statistical Methods",
                difficulty="intermediate",
                overview="CPI and index numbers",
            ),
        ]
    )
    session.commit()


def test_evidence_is_idempotent_and_drives_gaps_and_recommendations():
    client, session = _client()
    try:
        _seed_taxonomy(session)
        evidence = {
            "event_id": "evt-1",
            "user_id": 7,
            "competency_code": "price_statistics",
            "domain_code": "statistical",
            "level": 3.0,
            "source_type": "statistical_assessment",
            "source_id": "attempt-1",
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {"engine_version": "1"},
        }
        assert client.post("/v1/evidence", json=evidence).json()["status"] == "accepted"
        assert client.post("/v1/evidence", json=evidence).json()["status"] == "duplicate"
        assert session.scalar(select(func.count(Evidence.id))) == 1

        analysis = client.post(
            "/v1/competency/analyze",
            json={"target_levels": {"statistical": 4, "technical": 2}},
        ).json()
        gaps = {row["domain_code"]: row for row in analysis["gaps"]}
        assert gaps["statistical"]["current_level"] == 3.0
        assert gaps["statistical"]["gap"] == 1.0
        assert gaps["technical"]["gap"] == 2.0

        generated = client.post("/v1/recommendations/generate").json()
        assert generated[0]["course_id"] == 31
        assert generated[0]["status"] == "pending"
        updated = client.patch(
            f"/v1/recommendations/{generated[0]['id']}", json={"status": "dismissed"}
        )
        assert updated.status_code == 200
        assert session.scalar(select(Recommendation.status)) == "dismissed"
        assert session.scalar(select(func.count(Gap.id))) == 2
    finally:
        app.dependency_overrides.clear()
        session.close()


def test_evidence_rejects_unknown_competency():
    client, session = _client()
    try:
        _seed_taxonomy(session)
        response = client.post(
            "/v1/evidence",
            json={
                "event_id": "evt-x",
                "user_id": 7,
                "competency_code": "invented",
                "domain_code": "statistical",
                "level": 5,
                "source_type": "test",
                "source_id": "x",
                "observed_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()
        session.close()
