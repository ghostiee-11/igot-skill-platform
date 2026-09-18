from dataclasses import dataclass
import re


SERVICE_NAMES = frozenset({"identity", "learning", "assessment", "competency", "ai", "content", "labs"})


@dataclass(frozen=True)
class RouteTarget:
    service: str
    path: str


@dataclass(frozen=True)
class LegacyRoute:
    methods: frozenset[str]
    pattern: re.Pattern[str]
    service: str
    upstream_template: str

    def match(self, method: str, path: str) -> RouteTarget | None:
        if method.upper() not in self.methods:
            return None
        matched = self.pattern.fullmatch(path)
        if matched is None:
            return None
        return RouteTarget(self.service, self.upstream_template.format(**matched.groupdict()))


def _route(methods: str, pattern: str, service: str, upstream: str) -> LegacyRoute:
    return LegacyRoute(frozenset(methods.split("|")), re.compile(pattern), service, upstream)


# Operation allow-list from baseline 7123bd3. Unknown and not-yet-declared
# operations are rejected at the edge instead of being routed by loose prefix.
LEGACY_ROUTES: tuple[LegacyRoute, ...] = (
    _route("POST", r"auth/(?P<action>login|register|forgot-password)", "identity", "/v1/auth/{action}"),
    _route("GET", r"auth/me", "identity", "/v1/auth/me"),
    _route("GET", r"onboarding/status", "identity", "/v1/onboarding/status"),
    _route("POST", r"onboarding/save", "identity", "/v1/onboarding/save"),
    _route("GET|PUT", r"profile", "identity", "/v1/profile/"),
    _route("GET", r"discover/courses", "learning", "/v1/discover/courses"),
    _route("GET", r"courses/(?P<course_id>[^/]+)", "learning", "/v1/courses/{course_id}"),
    _route("POST", r"courses/(?P<course_id>[^/]+)/enroll", "learning", "/v1/courses/{course_id}/enroll"),
    _route("GET", r"learning/course/(?P<course_id>[^/]+)/player", "learning", "/v1/learning/course/{course_id}/player"),
    _route("POST", r"learning/lesson/(?P<lesson_id>[^/]+)/(?P<action>complete|activity)", "learning", "/v1/learning/lesson/{lesson_id}/{action}"),
    _route("GET", r"dashboard/summary", "learning", "/v1/dashboard/summary"),
    _route("GET", r"assessments/(?P<assessment_id>[^/]+)", "assessment", "/v1/assessments/{assessment_id}"),
    _route("POST", r"assessments/(?P<assessment_id>[^/]+)/submit", "assessment", "/v1/assessments/{assessment_id}/submit"),
    _route("GET", r"admin/overview", "learning", "/v1/admin/overview"),
    _route("POST", r"admin/assign-course", "learning", "/v1/admin/assign-course"),
    _route("GET|POST", r"admin/courses", "learning", "/v1/admin/courses"),
    _route("GET", r"admin/competency-analytics", "competency", "/v1/admin/competency-analytics"),
    _route("POST", r"admin/courses/(?P<course_id>[^/]+)/reindex", "competency", "/v1/admin/courses/{course_id}/reindex"),
    _route("GET", r"competency/domains/(?P<domain_code>[^/]+)", "competency", "/v1/competency/domains/{domain_code}"),
    _route("POST", r"competency/analyze", "competency", "/v1/competency/analyze"),
    _route("GET", r"competency/(?P<view>profile|gaps)", "competency", "/v1/competency/{view}"),
    _route("GET", r"recommendations", "competency", "/v1/recommendations"),
    _route("POST", r"recommendations/generate", "competency", "/v1/recommendations/generate"),
    _route("PATCH", r"recommendations/(?P<recommendation_id>[^/]+)", "competency", "/v1/recommendations/{recommendation_id}"),
    _route("POST", r"quiz/generate", "assessment", "/v1/quiz/generate"),
    _route("GET", r"quiz", "assessment", "/v1/quiz"),
    _route("GET|DELETE", r"quiz/(?P<quiz_id>[^/]+)", "assessment", "/v1/quiz/{quiz_id}"),
    _route("POST", r"quiz/(?P<quiz_id>[^/]+)/submit", "assessment", "/v1/quiz/{quiz_id}/submit"),
    _route("GET", r"quiz/(?P<quiz_id>[^/]+)/attempts", "assessment", "/v1/quiz/{quiz_id}/attempts"),
    _route("GET", r"stats-engine/health", "assessment", "/v1/stats-engine/health"),
    _route("POST", r"stats/calculate", "assessment", "/v1/stats/calculate"),
    _route("POST", r"charts/generate", "assessment", "/v1/charts/generate"),
    _route("POST", r"questions/(?P<action>generate|next|submit)", "assessment", "/v1/questions/{action}"),
    _route("GET", r"competencies", "assessment", "/v1/competencies"),
    _route("GET", r"competencies/(?P<competency_id>[^/]+)", "assessment", "/v1/competencies/{competency_id}"),
    _route("GET", r"users/(?P<user_id>[^/]+)/competencies", "assessment", "/v1/users/{user_id}/competencies"),
    _route("GET", r"behavioural/courses", "assessment", "/v1/behavioural/courses"),
    _route("GET", r"behavioural/courses/(?P<course_id>[^/]+)/cases", "assessment", "/v1/behavioural/courses/{course_id}/cases"),
    _route("POST", r"behavioural/courses/(?P<course_id>[^/]+)/generate-case", "assessment", "/v1/behavioural/courses/{course_id}/generate-case"),
    _route("GET", r"behavioural/corpus", "assessment", "/v1/behavioural/corpus"),
    _route("GET", r"behavioural/corpus/(?P<document_id>[^/]+)", "assessment", "/v1/behavioural/corpus/{document_id}"),
    _route("GET", r"behavioural/cases", "assessment", "/v1/behavioural/cases"),
    _route("GET", r"behavioural/cases/(?P<case_id>[^/]+)", "assessment", "/v1/behavioural/cases/{case_id}"),
    _route("POST", r"behavioural/cases/generate", "assessment", "/v1/behavioural/cases/generate"),
    _route("POST", r"behavioural/session/start", "assessment", "/v1/behavioural/session/start"),
    _route("GET", r"behavioural/session/(?P<session_id>[^/]+)/(?P<action>current|summary)", "assessment", "/v1/behavioural/session/{session_id}/{action}"),
    _route("POST", r"behavioural/session/(?P<session_id>[^/]+)/submit", "assessment", "/v1/behavioural/session/{session_id}/submit"),
    _route("POST", r"behavioural/interview/(?P<action>transcribe|start|turn|end)", "assessment", "/v1/behavioural/interview/{action}"),
    _route("POST", r"behavioural/interview/(?P<session_id>[^/]+)/end", "assessment", "/v1/behavioural/interview/{session_id}/end"),
    _route("POST", r"technical-courses/process", "content", "/v1/technical-courses/process"),
    _route("POST", r"technical-courses/(?P<action>objectives|decide-mode|match-template)", "assessment", "/v1/technical-courses/{action}"),
    _route("GET", r"technical-courses/templates", "assessment", "/v1/technical-courses/templates"),
    _route("GET", r"technical-courses/labs", "assessment", "/v1/technical-courses/labs"),
    _route("POST", r"technical-courses/labs/generate", "assessment", "/v1/technical-courses/labs/generate"),
    _route("GET", r"technical-courses/labs/(?P<lab_id>[^/]+)", "assessment", "/v1/technical-courses/labs/{lab_id}"),
    _route("POST", r"technical-courses/labs/(?P<lab_id>[^/]+)/(?P<action>solution|validate|assistant)", "assessment", "/v1/technical-courses/labs/{lab_id}/{action}"),
    _route("POST", r"technical-courses/pipeline/run-full", "assessment", "/v1/technical-courses/pipeline/run-full"),
    _route("POST", r"technical-courses/labs/(?P<lab_id>[^/]+)/execute", "labs", "/v1/technical-courses/labs/{lab_id}/execute"),
    _route("POST", r"technical-courses/sandbox/execute-code", "labs", "/v1/technical-courses/sandbox/execute-code"),
    _route("POST", r"technical-courses/notebook/export", "labs", "/v1/technical-courses/notebook/export"),
    _route("GET", r"digital-governance/scenarios", "assessment", "/v1/digital-governance/scenarios"),
    _route("GET", r"digital-governance/scenarios/(?P<scenario_id>[^/]+)", "assessment", "/v1/digital-governance/scenarios/{scenario_id}"),
    _route("POST", r"digital-governance/scenarios/session/start", "assessment", "/v1/digital-governance/scenarios/session/start"),
    _route("POST", r"digital-governance/scenarios/session/(?P<session_id>[^/]+)/answer", "assessment", "/v1/digital-governance/scenarios/session/{session_id}/answer"),
    _route("GET", r"digital-governance/scenarios/session/(?P<session_id>[^/]+)/summary", "assessment", "/v1/digital-governance/scenarios/session/{session_id}/summary"),
    _route("GET", r"digital-governance/sandbox/(?P<resource>challenges|knowledge-base|competencies)", "assessment", "/v1/digital-governance/sandbox/{resource}"),
    _route("POST", r"digital-governance/sandbox/(?P<action>generate|generate-from-topic)", "assessment", "/v1/digital-governance/sandbox/{action}"),
    _route("POST", r"digital-governance/sandbox/session/start", "labs", "/v1/digital-governance/sandbox/session/start"),
    _route("GET", r"digital-governance/sandbox/session/(?P<session_id>[^/]+)", "labs", "/v1/digital-governance/sandbox/session/{session_id}"),
    _route("POST", r"digital-governance/sandbox/session/(?P<session_id>[^/]+)/stop", "labs", "/v1/digital-governance/sandbox/session/{session_id}/stop"),
    _route("POST", r"digital-governance/sandbox/session/(?P<action>submit-flag|unlock-hint)", "labs", "/v1/digital-governance/sandbox/session/{action}"),
    _route("POST", r"agents/chat", "ai", "/v1/agents/chat"),
)


def resolve_legacy_path(path: str, method: str = "GET") -> RouteTarget | None:
    normalized = path.strip("/")
    if normalized.startswith("v1/"):
        normalized = normalized[3:]
    for route in LEGACY_ROUTES:
        target = route.match(method, normalized)
        if target is not None:
            return target
    return None


def resolve_namespaced_path(service: str, path: str) -> RouteTarget | None:
    if service not in SERVICE_NAMES:
        return None
    normalized = path.strip("/")
    suffix = f"/{normalized}" if normalized else ""
    return RouteTarget(service=service, path=f"/v1{suffix}")
