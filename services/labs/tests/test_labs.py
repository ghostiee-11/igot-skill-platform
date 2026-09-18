from dataclasses import dataclass

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from igot_labs import main
from igot_labs.database import Base, get_db
from igot_labs.security import Principal, principal


@dataclass
class FakeProvisioned:
    workspace_id: str = "workspace-1"
    target_ids: list[str] = None
    network_id: str = "network-1"
    workspace_host: str = "igot-workspace-session"

    def __post_init__(self):
        self.target_ids = self.target_ids or ["target-1"]


class FakeRuntime:
    terminated: list[tuple] = []

    def health(self):
        return True

    def provision(self, session_id, target_images):
        if not set(target_images) <= {"igot/target-demo:local"}:
            raise ValueError("target image is not allowed")
        return FakeProvisioned()

    def execute(self, container_id, argv):
        assert container_id == "workspace-1"
        return {"exit_code": 0, "stdout": "ok\n", "stderr": "", "truncated": False}

    def terminate(self, workspace_id, target_ids, network_id):
        self.terminated.append((workspace_id, target_ids, network_id))

    def archive(self, container_id, path="/workspace"):
        return b"archive", {"name": "workspace"}


def _client(monkeypatch) -> tuple[TestClient, Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    ).execution_options(schema_translate_map={"labs": None})
    Base.metadata.create_all(engine)
    session = Session(engine, expire_on_commit=False)

    def test_db():
        yield session

    monkeypatch.setattr(main, "DockerRuntime", FakeRuntime)
    main.app.dependency_overrides[get_db] = test_db
    main.app.dependency_overrides[principal] = lambda: Principal(7, "learner")
    return TestClient(main.app), session


def test_session_ownership_access_execution_and_termination(monkeypatch):
    client, session = _client(monkeypatch)
    try:
        created = client.post(
            "/v1/sessions",
            json={"lab_id": "lab-1", "target_images": ["igot/target-demo:local"]},
        )
        assert created.status_code == 201
        session_id = created.json()["id"]
        assert created.json()["status"] == "running"

        grant = client.post(f"/v1/sessions/{session_id}/access")
        assert grant.status_code == 201
        token = grant.json()["access_url"].split("/")[-2]
        authorized = client.get(f"/v1/lab-access/{token}/notebook")
        assert authorized.status_code == 200
        assert authorized.json()["workspace_host"] == "igot-workspace-session"

        executed = client.post(
            f"/v1/sessions/{session_id}/execute", json={"argv": ["python", "-c", "print('ok')"]}
        )
        assert executed.json()["stdout"] == "ok\n"
        assert client.post(f"/v1/sessions/{session_id}/terminate").json()["status"] == "terminated"

        main.app.dependency_overrides[principal] = lambda: Principal(8, "learner")
        assert client.get(f"/v1/sessions/{session_id}").status_code == 404
    finally:
        main.app.dependency_overrides.clear()
        session.close()


def test_target_images_are_not_accepted_from_outside_allowlist(monkeypatch):
    client, session = _client(monkeypatch)
    try:
        response = client.post(
            "/v1/sessions", json={"lab_id": "lab-1", "target_images": ["unknown/image:latest"]}
        )
        assert response.status_code == 503
    finally:
        main.app.dependency_overrides.clear()
        session.close()
