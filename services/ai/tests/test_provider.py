from fastapi.testclient import TestClient

from igot_ai.main import app
from igot_ai.providers import extract_json


def test_extract_json_from_fence():
    assert extract_json('```json\n{"ok": true}\n```') == {"ok": True}


def test_agent_uses_deterministic_fallback_without_provider_keys():
    response = TestClient(app).post(
        "/v1/agents/chat",
        json={"message": "Explain CPI inflation", "context": "Price statistics"},
    )
    assert response.status_code == 200
    assert response.json()["source"] == "deterministic-fallback"
    assert "CPI" in response.json()["response"]


def test_completion_requires_authentication():
    response = TestClient(app).post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "Hello"}]},
    )
    assert response.status_code == 401
