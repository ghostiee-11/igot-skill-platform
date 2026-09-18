from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from types import SimpleNamespace

from igot_identity.adapters.database import Base, get_db
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
