from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from types import SimpleNamespace

from igot_identity.adapters.database import Base, get_db
from igot_identity.api import routes
from igot_identity.application import security
from igot_identity.domain.models import User
from igot_identity.main import app


def _client(monkeypatch) -> tuple[TestClient, Session]:
    monkeypatch.setattr(
        security,
        "settings",
        SimpleNamespace(
            jwt_secret="test-secret-that-is-longer-than-thirty-two-characters",
            jwt_algorithm="HS256",
            access_token_expire_minutes=60,
        ),
    )
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    ).execution_options(schema_translate_map={"identity": None})
    Base.metadata.create_all(engine)
    session = Session(engine, expire_on_commit=False)

    def test_db():
        yield session

    app.dependency_overrides[get_db] = test_db
    return TestClient(app), session


def test_register_login_and_profile(monkeypatch):
    client, session = _client(monkeypatch)
    try:
        created = client.post(
            "/v1/auth/register",
            json={
                "email": "user@example.gov.in",
                "password": "secret",
                "full_name": "User",
                "role": "learner",
            },
        )
        assert created.status_code == 201
        token = created.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        updated = client.put(
            "/v1/profiles/me",
            headers=headers,
            json={"designation": "Director", "areas_of_interest": ["data"]},
        )
        assert updated.status_code == 200
        profile = client.get("/v1/profiles/me", headers=headers).json()
        assert profile["profile"]["designation"] == "Director"

        escalated = client.post(
            "/v1/auth/register",
            json={
                "email": "attacker@example.gov.in",
                "password": "secret",
                "full_name": "Attacker",
                "role": "admin",
            },
        )
        assert escalated.status_code == 422

        recovery = client.post(
            "/v1/auth/forgot-password",
            json={"email": "user@example.gov.in"},
        )
        assert recovery.status_code == 503

        user = session.scalar(select(User).where(User.email == "user@example.gov.in"))
        assert user is not None
        user.is_active = False
        session.commit()
        inactive = client.post(
            "/v1/auth/login",
            json={"email": "user@example.gov.in", "password": "secret"},
        )
        assert inactive.status_code == 403
    finally:
        app.dependency_overrides.clear()
        session.close()


def test_configured_demo_learner_is_created_and_repaired(monkeypatch):
    client, session = _client(monkeypatch)
    monkeypatch.setattr(
        routes,
        "settings",
        SimpleNamespace(
            demo_accounts_enabled=True,
            demo_learner_email="rajesh.kumar@mospi.gov.in",
            demo_learner_password="Learner@123",
            demo_learner_name="Rajesh Kumar",
        ),
    )
    credentials = {"email": "rajesh.kumar@mospi.gov.in", "password": "Learner@123"}
    try:
        first = client.post("/v1/auth/login", json=credentials)
        assert first.status_code == 200
        assert first.json()["role"] == "learner"
        assert first.json()["onboarding_completed"] is True

        user = session.scalar(select(User).where(User.email == credentials["email"]))
        user.password_hash = security.hash_password("wrong-password")
        user.role = "admin"
        user.is_active = False
        user.profile.onboarding_completed = False
        session.commit()

        repaired = client.post("/v1/auth/login", json=credentials)
        assert repaired.status_code == 200
        session.refresh(user)
        assert user.role == "learner"
        assert user.is_active is True
        assert user.profile.onboarding_completed is True
        assert security.verify_password("Learner@123", user.password_hash)

        wrong = client.post(
            "/v1/auth/login",
            json={"email": credentials["email"], "password": "not-the-demo-password"},
        )
        assert wrong.status_code == 401
    finally:
        app.dependency_overrides.clear()
        session.close()
