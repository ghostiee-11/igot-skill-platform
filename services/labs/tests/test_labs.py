from dataclasses import dataclass
from contextlib import nullcontext

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from igot_labs import main
from igot_labs.database import Base, LegacyCyberSession, get_db
from igot_labs.security import Principal, internal, principal


@dataclass
class FakeProvisioned:
    workspace_id: str = "workspace-1"
    target_ids: list[str] = None
    network_id: str = "network-1"
    workspace_host: str = "igot-workspace-session"
    public_port: int | None = None

    def __post_init__(self):
        self.target_ids = self.target_ids or ["target-1"]


class FakeRuntime:
    terminated: list[tuple] = []

    def health(self):
        return True

    def provision(self, session_id, target_images, challenge=None):
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


def test_cyber_incident_lifecycle_is_owned_and_flag_is_private(monkeypatch):
    client, session = _client(monkeypatch)
    challenge = {"id": "01-soc-auth-investigation", "title": "SOC incident", "category": "SOC", "difficulty": "Beginner",
                 "points": 100, "duration_minutes": 45, "competency_id": "soc_investigation", "objectives": ["Investigate"],
                 "scenario_md": "Inspect the logs", "hints": [{"id": 1, "content": "Look at failures", "penalty": 15}],
                 "artifacts": {"auth_events.json": "[]"}, "notebook_code": "import marimo\napp = marimo.App()", "flag": "FLAG{verified}"}
    class FakeResponse:
        def raise_for_status(self): pass
        def json(self): return challenge.copy()
    class FakeAsyncClient:
        def __init__(self, **_): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *_): pass
        async def get(self, *_args, **_kwargs): return FakeResponse()
    monkeypatch.setattr(main.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(main.socket, "create_connection", lambda *_args, **_kwargs: nullcontext())
    try:
        started = client.post("/v1/digital-governance/sandbox/session/start", json={"challenge_id":challenge["id"]})
        assert started.status_code == 201
        result = started.json();session_id=result["session_id"]
        assert result["marimo_url"].startswith("http://localhost:8107/v1/cyber-console/")
        assert "verified" not in str(result)
        assert session.get(LegacyCyberSession,session_id).flag=="FLAG{verified}"
        hint=client.post("/v1/digital-governance/sandbox/session/unlock-hint",json={"session_id":session_id,"hint_id":1})
        assert hint.json()["remaining_points"]==85
        wrong=client.post("/v1/digital-governance/sandbox/session/submit-flag",json={"session_id":session_id,"flag":"FLAG{fake}"})
        assert not wrong.json()["correct"]
        correct=client.post("/v1/digital-governance/sandbox/session/submit-flag",json={"session_id":session_id,"flag":"FLAG{verified}"})
        assert correct.json()["points_awarded"]==85
        assert client.get("/v1/digital-governance/sandbox/competencies").json()["total_score"]==85
        main.app.dependency_overrides[principal]=lambda:Principal(8,"learner")
        assert client.get(f"/v1/digital-governance/sandbox/session/{session_id}").status_code==404
        main.app.dependency_overrides[principal]=lambda:Principal(7,"learner")
        assert client.post(f"/v1/digital-governance/sandbox/session/{session_id}/stop").status_code==200
    finally:
        main.app.dependency_overrides.clear();session.close()


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
    main.app.dependency_overrides[internal] = lambda: None
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


def test_ephemeral_code_and_notebook_export(monkeypatch):
    client, session = _client(monkeypatch)
    FakeRuntime.terminated.clear()
    try:
        cell=client.post("/v1/technical-courses/sandbox/execute-code",json={"code":"print('ok')"})
        assert cell.status_code==200 and cell.json()["success"] is True
        graded=client.post("/v1/code/grade",json={"code":"def solve(): return 1","tests":[{"name":"works","test_code":"assert solve() == 1"}]})
        assert graded.status_code==200 and graded.json()["all_passed"] is True
        assert len(FakeRuntime.terminated)==2
        exported=client.post("/v1/technical-courses/notebook/export",json={"title":"Example Lab","cells":[{"type":"code","content":"print(1)"}]})
        assert exported.status_code==200
        assert exported.json()["filename"]=="example_lab.ipynb"
    finally:
        main.app.dependency_overrides.clear()
        session.close()
