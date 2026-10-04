import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import app
from app.core.seed_competencies import seed_competency_taxonomy, seed_evidence_mapping
from app.models.models import User, Course, CompetencyDomain, GapAnalysis


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
    seed_competency_taxonomy(db)
    seed_evidence_mapping(db)
    try:
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


def test_generate_and_list_recommendations(client, db_session, monkeypatch):
    user = User(email="officer@example.gov.in", password_hash="x", full_name="Officer")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    domain = db_session.query(CompetencyDomain).filter_by(code="technical").first()
    db_session.add(GapAnalysis(user_id=user.id, domain_id=domain.id, target_level=4.0, current_level=2.0, gap=2.0))
    course = Course(title="Intro to Python", overview="x", instructor="x", organization="ISTM", category="technical")
    db_session.add(course)
    db_session.commit()

    token = create_access_token({"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    generate_resp = client.post("/api/recommendations/generate", headers=headers)
    assert generate_resp.status_code == 200
    assert len(generate_resp.json()) >= 1

    list_resp = client.get("/api/recommendations", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1
    assert list_resp.json()[0]["status"] == "pending"


def test_recommendations_require_auth(client):
    resp = client.get("/api/recommendations")
    assert resp.status_code == 401
