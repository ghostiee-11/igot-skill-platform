import pytest

from igot_gateway.routing import RouteTarget, resolve_legacy_path, resolve_namespaced_path


def test_routes_identity_compatibility_path() -> None:
    target = resolve_legacy_path("auth/login", "POST")
    assert target is not None
    assert (target.service, target.path) == ("identity", "/v1/auth/login")


def test_longest_prefix_routes_lab_execution_to_labs() -> None:
    target = resolve_legacy_path("technical-courses/labs/lab-1/execute", "POST")
    assert target is not None
    assert target.service == "labs"


def test_assessment_family_stays_with_assessment() -> None:
    target = resolve_legacy_path("behavioural/interview/start", "POST")
    assert target is not None
    assert target.service == "assessment"


def test_unknown_legacy_path_is_rejected() -> None:
    assert resolve_legacy_path("unowned/action") is None


def test_known_family_unknown_operation_is_rejected() -> None:
    assert resolve_legacy_path("auth/delete-everyone", "DELETE") is None


def test_known_path_with_wrong_method_is_rejected() -> None:
    assert resolve_legacy_path("auth/login", "GET") is None


def test_api_v1_alias_is_normalized_without_a_second_route_registration() -> None:
    assert resolve_legacy_path("v1/auth/me", "GET") == resolve_legacy_path("auth/me", "GET")


@pytest.mark.parametrize(
    ("method", "path", "service", "upstream"),
    [
        ("POST", "auth/register", "identity", "/v1/auth/register"),
        ("POST", "onboarding/save", "identity", "/v1/onboarding/save"),
        ("PUT", "profile/", "identity", "/v1/profile/"),
        ("GET", "discover/courses", "learning", "/v1/discover/courses"),
        ("POST", "courses/7/enroll", "learning", "/v1/courses/7/enroll"),
        ("POST", "learning/lesson/9/activity", "learning", "/v1/learning/lesson/9/activity"),
        ("GET", "admin/competency-analytics", "competency", "/v1/admin/competency-analytics"),
        ("POST", "admin/courses/2/reindex", "competency", "/v1/admin/courses/2/reindex"),
        ("POST", "stats/calculate", "assessment", "/v1/stats/calculate"),
        ("GET", "competencies", "assessment", "/v1/competencies"),
        ("GET", "users/4/competencies", "assessment", "/v1/users/4/competencies"),
        ("POST", "quiz/q1/submit", "assessment", "/v1/quiz/q1/submit"),
        ("POST", "behavioural/interview/session-1/end", "assessment", "/v1/behavioural/interview/session-1/end"),
        ("POST", "technical-courses/process", "content", "/v1/technical-courses/process"),
        ("POST", "technical-courses/labs/l1/assistant", "assessment", "/v1/technical-courses/labs/l1/assistant"),
        ("POST", "technical-courses/sandbox/execute-code", "labs", "/v1/technical-courses/sandbox/execute-code"),
        ("POST", "digital-governance/scenarios/session/s1/answer", "assessment", "/v1/digital-governance/scenarios/session/s1/answer"),
        ("POST", "digital-governance/sandbox/session/s1/stop", "labs", "/v1/digital-governance/sandbox/session/s1/stop"),
        ("POST", "agents/chat", "ai", "/v1/agents/chat"),
    ],
)
def test_baseline_route_families_have_explicit_owners(method: str, path: str, service: str, upstream: str) -> None:
    assert resolve_legacy_path(path, method) == RouteTarget(service, upstream)


def test_namespaced_route_removes_service_from_upstream_path() -> None:
    target = resolve_namespaced_path("content", "sources/source-1")
    assert target is not None
    assert target.path == "/v1/sources/source-1"


def test_unknown_service_is_rejected() -> None:
    assert resolve_namespaced_path("other", "health") is None
