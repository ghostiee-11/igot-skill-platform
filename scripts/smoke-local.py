"""Live local Compose smoke check. Creates a separate test learner and test records."""
import json
import secrets
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://localhost:8000"
TOKEN = None


def request(path, method="GET", data=None, form=None):
    headers = {}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    payload = None
    if data is not None:
        payload = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    if form is not None:
        payload = urlencode(form).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    try:
        with urlopen(Request(BASE+path, data=payload, headers=headers, method=method), timeout=90) as response:
            body = response.read()
            return json.loads(body) if body else None
    except HTTPError as exc:
        raise RuntimeError(f"{method} {path}: HTTP {exc.code}: {exc.read().decode()[:500]}") from None


def main():
    global TOKEN
    fixtures = json.loads((ROOT / "infra/seed/catalogue.json").read_text(encoding="utf-8"))
    request("/health")
    request("/api/auth/login", "POST", {"email":"rajesh.kumar@mospi.gov.in", "password":"Learner@123"})
    print("PASS: standard learner login", flush=True)
    account = request("/api/auth/register", "POST", {"email":f"local-smoke-{secrets.token_hex(5)}@example.gov.in",
                      "password":secrets.token_urlsafe(18), "full_name":"Local Smoke Learner", "role":"learner"})
    TOKEN = account["access_token"]
    request("/api/onboarding/save", "POST", {"education":"Statistics", "designation":"SSO", "department":"MoSPI",
                                             "job_role":"Statistical analysis", "areas_of_interest":["CPI"]})
    catalogue = request("/api/discover/courses")
    assert len(catalogue["courses"]) >= 4
    for course in catalogue["courses"]:
        detail = request(f"/api/courses/{course['id']}")
        assert detail["modules"] and sum(len(m["lessons"]) for m in detail["modules"]) > 0
        request(f"/api/courses/{course['id']}/enroll", "POST", {})
        player = request(f"/api/learning/course/{course['id']}/player")
        assert player["current_lesson"]["content"]
    print("PASS: onboarding, catalogue, enrolment and lesson player for all four courses", flush=True)
    player = request("/api/learning/course/2/player")
    request(f"/api/learning/lesson/{player['current_lesson']['id']}/complete", "POST", {})
    exam = request("/api/assessments/2")
    assert "correct_option_index" not in json.dumps(exam)
    answers = {str(q["id"]):q["correct_option_index"] for q in fixtures["assessment"]["questions"] if q["assessment_id"] == 2}
    result = request("/api/assessments/2/submit", "POST", {"answers":answers})
    assert result["passed"] and result["score_percent"] == 100
    for _ in range(20):
        certificates = request("/v1/learning/certificates")
        if any(c["certificate_id"] == result["certificate_id"] for c in certificates):
            break
        time.sleep(1)
    else:
        raise AssertionError("Assessment event did not create a certificate")
    summary = request("/api/dashboard/summary")
    assert summary["my_learning_progress"]["completed_count"] >= 1
    assert summary["learner"]["full_name"] == "Local Smoke Learner"
    public_profile = request("/api/profile/")
    assert any(c["certificate_id"] == result["certificate_id"] for c in public_profile["certificates"])
    print("PASS: assessment grading, durable certificate and dashboard completion", flush=True)
    profile = request("/api/competency/analyze", "POST", {})
    assert len(profile["gaps"]) == 4
    request("/api/recommendations/generate", "POST", {})
    print("PASS: competency analysis and recommendations", flush=True)
    question = request("/api/questions/next", "POST", {"competency_id":"price_statistics", "question_type":"mcq"})
    assert "correct_answer" not in question and question["options"]
    original = next(q for q in fixtures["assessment"]["stat_engine_questions"] if q["question_id"] == question["question_id"])
    feedback = request("/api/questions/submit", "POST", {"question_id":question["question_id"], "submitted_answer":original["correct_option_id"]})
    assert feedback["correct"]
    print("PASS: adaptive statistical questions and grading", flush=True)
    labs = request("/api/technical-courses/labs")
    assert len(labs) == 6
    lab = next(t for t in fixtures["assessment"]["technical_lab_templates"] if t["id"] == labs[0]["template_id"])
    graded = request(f"/api/technical-courses/labs/{labs[0]['id']}/execute", "POST", {"code":lab["solution_template"]})
    assert graded["total_tests_count"] > 0 and graded["passed_tests_count"] == graded["total_tests_count"]
    print("PASS: isolated Docker technical lab execution and grading", flush=True)
    session = request("/api/digital-governance/sandbox/session/start", "POST", {"challenge_id":"01-soc-auth-investigation", "duration_minutes":5})
    try:
        with urlopen(session["marimo_url"], timeout=30) as response:
            assert response.status == 200 and b"marimo" in response.read().lower()
        assert "flag" not in session
        print("PASS: cyber incident Docker lifecycle and notebook ingress", flush=True)
    finally:
        request(f"/api/digital-governance/sandbox/session/{session['session_id']}/stop", "POST", {})
    source = ("Consumer price statistics measure changes in household consumption prices. "
              "The consumer price index uses expenditure weights from a representative household basket. "
              "Price relatives compare current prices with the approved base-period prices. "
              "Field officers validate source data before statistical compilation.")
    quiz = request("/api/quiz/generate", "POST", form={"text":source, "title":"Local smoke quiz", "num_questions":3})
    assert quiz["questions"]
    request(f"/api/quiz/{quiz['id']}")
    print("PASS: generated quiz and delivery", flush=True)
    cases = request("/api/behavioural/cases")
    scenarios = request("/api/digital-governance/scenarios")
    assert cases and scenarios
    interview = request("/api/behavioural/interview/start", "POST", {"course_id":1, "target_duration_minutes":25})
    assert interview["initial_ai_question"]
    request("/api/behavioural/interview/turn", "POST", {"session_id":interview["session_id"], "officer_response":"I would disclose the conflict in writing and seek guidance from the competent authority.", "elapsed_seconds":60})
    report = request("/api/behavioural/interview/end", "POST", {"session_id":interview["session_id"]})
    assert report
    print("PASS: behavioural/scenario catalogues and interview turn/report", flush=True)
    print("Local live smoke check complete; test activity belongs to a separate Local Smoke Learner.", flush=True)


if __name__ == "__main__":
    main()
