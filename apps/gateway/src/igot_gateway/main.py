import asyncio
from contextlib import asynccontextmanager
from uuid import uuid4

import httpx
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .routing import RouteTarget, resolve_legacy_path, resolve_namespaced_path


HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "host",
    "content-length",
    "content-encoding",
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.client = httpx.AsyncClient(timeout=settings.request_timeout_seconds, follow_redirects=False)
    yield
    await app.state.client.aclose()


app = FastAPI(title="iGOT API Gateway", version="0.1.0", lifespan=lifespan)
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _forward_request_headers(request: Request) -> list[tuple[bytes, bytes]]:
    headers = [(key, value) for key, value in request.headers.raw if key.decode("latin-1").lower() not in HOP_BY_HOP_HEADERS]
    if not any(key.lower() == b"x-request-id" for key, _ in headers):
        headers.append((b"x-request-id", str(uuid4()).encode("ascii")))
    return headers


def _forward_response_headers(headers: httpx.Headers) -> list[tuple[bytes, bytes]]:
    return [
        (key, value)
        for key, value in headers.raw
        if key.decode("latin-1").lower() not in HOP_BY_HOP_HEADERS
    ]


async def _proxy(request: Request, target: RouteTarget) -> Response:
    service_url = settings.service_urls[target.service]
    url = f"{service_url}{target.path}"
    try:
        upstream = await request.app.state.client.request(
            method=request.method,
            url=url,
            # QueryParams is a multidict, but passing it directly through some
            # httpx versions collapses repeated keys. Filters such as
            # `tag=one&tag=two` must survive the gateway unchanged.
            params=request.query_params.multi_items(),
            content=await request.body(),
            headers=_forward_request_headers(request),
        )
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail=f"{target.service} service timed out") from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=503, detail=f"{target.service} service is unavailable") from exc

    response = Response(content=upstream.content, status_code=upstream.status_code)
    response.raw_headers = _forward_response_headers(upstream.headers)
    return response


async def _read_service(request: Request, service: str, path: str):
    try:
        response = await request.app.state.client.get(
            f"{settings.service_urls[service]}{path}", headers=_forward_request_headers(request)
        )
    except httpx.TimeoutException as exc:
        raise HTTPException(504, f"{service} service timed out") from exc
    except httpx.RequestError as exc:
        raise HTTPException(503, f"{service} service is unavailable") from exc
    try:
        data = response.json()
    except ValueError as exc:
        raise HTTPException(502, f"{service} returned an invalid response") from exc
    if not response.is_success:
        raise HTTPException(response.status_code, data.get("detail", f"{service} request failed") if isinstance(data, dict) else data)
    return data


async def _profile(request: Request) -> Response:
    identity = await _read_service(request, "identity", "/v1/profiles/me")
    certificates, skills = await asyncio.gather(
        _read_service(request, "learning", "/v1/certificates"),
        _read_service(request, "competency", "/v1/competency/skills"),
    )
    return JSONResponse({**identity, "certificates": certificates, "skills": skills})


async def _dashboard(request: Request) -> Response:
    identity, dashboard, skills = await asyncio.gather(
        _read_service(request, "identity", "/v1/profiles/me"),
        _read_service(request, "learning", "/v1/dashboard/summary"),
        _read_service(request, "competency", "/v1/competency/skills"),
    )
    profile = identity["profile"]
    dashboard["learner"].update(id=identity["user_id"], full_name=identity["full_name"], email=identity["email"],
                                role=identity["role"], designation=profile.get("designation") or "Civil Servant",
                                department=profile.get("department") or "Official Statistical System")
    target = profile.get("daily_goal_minutes") or 30
    dashboard["todays_goals"].update(target_minutes=target,
                                    percent=min(100, int(dashboard["todays_goals"]["achieved_minutes"] / target * 100)))
    dashboard["learning_streak"]["streak_days"] = profile.get("current_streak_days") or 0
    dashboard["competencies"] = {"skills_count": len(skills), "top_skills": skills[:5]}
    return JSONResponse(dashboard)


@app.get("/health", tags=["platform"])
@app.get("/api/health", tags=["platform"])
async def health() -> dict[str, str]:
    return {"status": "healthy", "service": "gateway"}


@app.get("/ready", tags=["platform"])
async def ready() -> dict[str, str]:
    return {"status": "ready", "service": "gateway"}


@app.api_route(
    "/api/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
    include_in_schema=False,
)
async def legacy_proxy(path: str, request: Request) -> Response:
    target = resolve_legacy_path(path, request.method)
    if target is None:
        raise HTTPException(status_code=404, detail="No service owns this legacy API path")
    if request.method == "GET":
        if target == RouteTarget("identity", "/v1/profile/"):
            return await _profile(request)
        if target == RouteTarget("learning", "/v1/dashboard/summary"):
            return await _dashboard(request)
    return await _proxy(request, target)


@app.api_route(
    "/v1/{service}/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
    include_in_schema=False,
)
async def namespaced_proxy(service: str, path: str, request: Request) -> Response:
    target = resolve_namespaced_path(service, path)
    if target is None:
        raise HTTPException(status_code=404, detail="Unknown service")
    return await _proxy(request, target)
