import httpx
from fastapi.testclient import TestClient

from igot_gateway.main import app


def test_profile_includes_owned_certificates_and_skills_and_dashboard_is_personalized():
    def handler(request):
        assert request.headers["authorization"] == "Bearer learner"
        data = {
            "/v1/profiles/me": {"user_id": 7, "full_name": "Rajesh Kumar", "email": "learner@example.gov.in",
                                 "role": "learner", "profile": {"designation":"SSO", "department":"MoSPI", "daily_goal_minutes":60}},
            "/v1/certificates": [{"certificate_id":"KARM-CERT-2-0007"}],
            "/v1/competency/skills": [{"name":"Price Statistics"}],
            "/v1/dashboard/summary": {"learner":{"full_name":"Learner"}, "todays_goals":{"achieved_minutes":20}, "learning_streak":{}},
        }[request.url.path]
        return httpx.Response(200, json=data)

    with TestClient(app) as client:
        client.app.state.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        profile = client.get("/api/profile/", headers={"Authorization":"Bearer learner"}).json()
        assert profile["certificates"][0]["certificate_id"] == "KARM-CERT-2-0007"
        assert profile["skills"][0]["name"] == "Price Statistics"
        dashboard = client.get("/api/dashboard/summary", headers={"Authorization":"Bearer learner"}).json()
        assert dashboard["learner"]["full_name"] == "Rajesh Kumar"
        assert dashboard["learner"]["designation"] == "SSO"
        assert dashboard["todays_goals"] == {"achieved_minutes":20,"target_minutes":60,"percent":33}


def test_profile_preserves_identity_rejection_and_does_not_hide_learning_failure():
    status = 401
    calls = []

    def handler(request):
        calls.append(request.url.path)
        if request.url.path == "/v1/profiles/me":
            return httpx.Response(status, json={"detail":"Expired session"} if status == 401 else {"profile":{}})
        if request.url.path == "/v1/certificates":
            raise httpx.ConnectError("learning unavailable")
        return httpx.Response(200, json=[])

    with TestClient(app) as client:
        client.app.state.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        assert client.get("/api/profile/").status_code == 401
        assert calls == ["/v1/profiles/me"]
        status = 200
        failed = client.get("/api/profile/")
        assert failed.status_code == 503
        assert failed.json()["detail"] == "learning service is unavailable"
