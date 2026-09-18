import gzip

import httpx
from fastapi.testclient import TestClient

from igot_gateway.main import app


def test_proxy_preserves_method_query_body_and_authorization() -> None:
    observed: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        observed.update(
            method=request.method,
            path=request.url.path,
            query=request.url.query.decode(),
            body=request.content,
            authorization=request.headers.get("authorization"),
        )
        return httpx.Response(201, json={"accepted": True}, headers={"x-request-id": "req-1"})

    with TestClient(app) as client:
        client.app.state.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        response = client.post(
            "/api/assessments/a-1/submit?mode=final",
            content=b'{"answer": 4}',
            headers={"content-type": "application/json", "authorization": "Bearer token"},
        )

    assert response.status_code == 201
    assert response.json() == {"accepted": True}
    assert observed == {
        "method": "POST",
        "path": "/v1/assessments/a-1/submit",
        "query": "mode=final",
        "body": b'{"answer": 4}',
        "authorization": "Bearer token",
    }


def test_proxy_preserves_duplicate_query_and_response_headers_without_stale_encoding() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.query.decode() == "tag=one&tag=two"
        assert request.headers["x-request-id"]
        return httpx.Response(
            200,
            content=gzip.compress(b'{"ok":true}'),
            headers=[
                ("content-type", "application/json"),
                ("content-encoding", "gzip"),
                ("content-length", "999"),
                ("set-cookie", "a=1"),
                ("set-cookie", "b=2"),
            ],
        )

    with TestClient(app) as client:
        client.app.state.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        response = client.get("/api/discover/courses?tag=one&tag=two")

    assert response.content == b'{"ok":true}'
    assert "content-encoding" not in response.headers
    assert response.headers.get_list("set-cookie") == ["a=1", "b=2"]


def test_api_v1_alias_uses_same_compatibility_mapping() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/auth/me"
        return httpx.Response(200, json={"id": 1})

    with TestClient(app) as client:
        client.app.state.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        response = client.get("/api/v1/auth/me")

    assert response.status_code == 200


def test_gateway_distinguishes_upstream_timeout_from_connection_failure() -> None:
    def timeout(_: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow")

    with TestClient(app) as client:
        client.app.state.client = httpx.AsyncClient(transport=httpx.MockTransport(timeout))
        response = client.get("/api/auth/me")

    assert response.status_code == 504
    assert response.json()["detail"] == "identity service timed out"
