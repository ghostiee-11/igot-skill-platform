from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from types import SimpleNamespace

from igot_assessment import main
from igot_assessment.database import Base, GeneratedBehaviouralCase, GeneratedQuiz, GeneratedQuizQuestion, OutboxEvent, SessionRecord, StatEngineMastery, StatEngineQuestion, TechnicalLabTemplate, get_db
from igot_assessment.engines import REGISTRY, public_state
from igot_assessment.security import Principal, current_principal, require_admin


def _definition() -> dict:
    return {
        "competency_codes": ["C1"],
        "items": [
            {
                "id": "q1",
                "text": "Choose the compliant action",
                "competency_code": "C1",
                "correct_option_index": 0,
                "options": [
                    {"id": "a", "text": "Correct", "compliance_delta": 100},
                    {"id": "b", "text": "Incorrect", "compliance_delta": 0},
                ],
            }
        ],
    }


def test_all_domains_emit_evidence_without_exposing_answer_keys():
    for name in ("statistical", "behavioural", "technical", "digital_governance"):
        engine = REGISTRY[name]
        state = engine.start(_definition())
        assert public_state(state)["current_item"]["options"] == [
            {"id": "a", "text": "Correct"},
            {"id": "b", "text": "Incorrect"},
        ]
        result = engine.finalize(engine.submit(state, {"option_id": "a"}))
        assert result["passed"]
        assert result["evidence"][0]["competency_code"] == "C1"


def _client(monkeypatch) -> tuple[TestClient, Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    ).execution_options(schema_translate_map={"assessment": None})
    Base.metadata.create_all(engine)
    session = Session(engine, expire_on_commit=False)

    def test_db():
        yield session

    learner = Principal(user_id=7, role="learner", full_name="Test Learner")
    administrator = Principal(user_id=1, role="admin", full_name="Administrator")
    main.app.dependency_overrides[get_db] = test_db
    main.app.dependency_overrides[current_principal] = lambda: learner
    main.app.dependency_overrides[require_admin] = lambda: administrator

    async def metadata(_: int) -> dict:
        return {"title": "Official Statistics", "organization": "MoSPI", "duration_hours": 3}

    monkeypatch.setattr(main, "course_metadata", metadata)
    return TestClient(main.app), session


def test_adaptive_question_is_private_and_mastery_is_persistent(monkeypatch):
    client, session = _client(monkeypatch)
    session.add(StatEngineQuestion(question_id="item-1", template_id="template", skill_id="price.price_relative",
        competency_id="price_statistics", question_type="mcq", difficulty="basic", prompt="Choose the index",
        parameters={"base": 10, "answer": 120}, correct_answer=120, tolerance=None,
        options_map={"A": [90, "inverted"], "B": [120, None]}, correct_option_id="B",
        explanation="Current over base.", unit=None, chart=None, seed=1))
    session.commit()
    question = client.post("/v1/questions/next", json={"user_id": "somebody-else", "competency_id": "price_statistics"})
    assert question.status_code == 200
    assert question.json()["data"] == {"base": 10}
    assert "correct_answer" not in str(question.json())
    result = client.post("/v1/questions/submit", json={"user_id": "somebody-else", "question_id": "item-1", "submitted_answer": "B"})
    assert result.status_code == 200
    assert result.json()["mastery"]["score"] == 10
    assert session.query(StatEngineMastery).one().user_id == 7
    assert client.post("/v1/questions/submit", json={"question_id": "item-1", "submitted_answer": "B"}).json()["mastery"]["score"] == 20
    main.app.dependency_overrides.clear()


def test_notice_generated_case_survives_cache_reset(monkeypatch):
    client, session = _client(monkeypatch)
    notice = "Officers must verify the source dataset and document the authority for each statistical release before publication."
    generated = client.post("/v1/behavioural/cases/generate", json={"raw_text": notice, "document_title": "Release Notice"})
    assert generated.status_code == 201
    case = generated.json()
    assert notice in case["initial_context"]
    assert session.get(GeneratedBehaviouralCase, case["id"])
    started = client.post("/v1/behavioural/session/start", json={"case_id": case["id"]})
    assert started.status_code == 201
    session_id = started.json()["session_id"]
    session.query(GeneratedBehaviouralCase).delete()
    session.commit()
    assert client.get(f"/v1/behavioural/session/{session_id}/current").status_code == 200
    assert client.post(f"/v1/behavioural/session/{session_id}/submit", json={"question_id": case["root_question_id"], "selected_option_id": "A"}).status_code == 200
    assert client.get(f"/v1/behavioural/session/{session_id}/summary").status_code == 200
    main.app.dependency_overrides.clear()


def test_course_case_uses_submitted_notice_and_is_private(monkeypatch):
    client, session = _client(monkeypatch)
    notice = "Verify the release register, notify the supervising officer, and preserve the signed record before publishing official figures."
    created = client.post("/v1/behavioural/courses/42/generate-case", json={"custom_notice_text": notice})
    assert created.status_code == 201
    case = created.json()
    assert case["course_id"] == 42
    assert notice in case["initial_context"]
    assert case["root_question_id"] != "q_ccs_root"
    assert client.get("/v1/behavioural/courses/42/cases").json()[-1]["id"] == case["id"]
    main.app.dependency_overrides[current_principal] = lambda: Principal(user_id=8, role="learner", full_name="Other")
    assert client.get(f"/v1/behavioural/cases/{case['id']}").status_code == 404
    assert client.post("/v1/behavioural/session/start", json={"case_id": case["id"]}).status_code == 404
    main.app.dependency_overrides.clear()


def test_adaptive_chart_shape(monkeypatch):
    client, session = _client(monkeypatch)
    chart = {"type": "bar", "title": "Index", "xAxis": {"field": "year", "label": "Year"},
             "yAxis": {"field": "index", "label": "Index"}, "data": [{"year": "2025", "index": 120}]}
    session.add(StatEngineQuestion(question_id="chart-1", template_id="chart", skill_id="price.chart",
        competency_id="price_statistics", question_type="chart_interpretation", difficulty="basic", prompt="Read the chart",
        parameters={"answer": "A"}, correct_answer="A", tolerance=None, options_map={"A": [120, None], "B": [100, "base"]},
        correct_option_id="A", explanation="Read the axis.", unit=None, chart=chart, seed=1))
    session.commit()
    response = client.post("/v1/questions/next", json={"competency_id": "price_statistics", "question_type": "chart_interpretation"})
    assert response.status_code == 200
    assert response.json()["chart"] == chart
    assert response.json()["data"] == {}
    main.app.dependency_overrides.clear()


def _assessment_payload() -> dict:
    return {
        "id": 91,
        "course_id": 11,
        "title": "Final assessment",
        "engine": "statistical",
        "time_limit_minutes": 20,
        "pass_threshold_percent": 70,
        "questions": [
            {
                "text": "What is the official answer?",
                "options": ["Correct", "Incorrect"],
                "correct_option_index": 0,
                "explanation": "The first option is correct.",
                "competency_code": "price_statistics",
            }
        ],
    }


def test_assessment_delivery_submission_and_idempotency(monkeypatch):
    client, session = _client(monkeypatch)
    try:
        assert client.post("/v1/assessments", json=_assessment_payload()).status_code == 201
        delivered = client.get("/v1/assessments/91").json()
        assert delivered["questions"][0]["options"] == ["Correct", "Incorrect"]
        assert "correct_option_index" not in delivered["questions"][0]

        headers = {"Idempotency-Key": "submission-1"}
        first = client.post("/v1/assessments/91/submit", json={"answers": {"1": 0}}, headers=headers)
        second = client.post("/v1/assessments/91/submit", json={"answers": {"1": 1}}, headers=headers)
        assert first.status_code == 200
        assert first.json() == second.json()
        assert first.json()["recipient_name"] == "Test Learner"
        assert first.json()["certificate_id"] == "KARM-CERT-11-0007"
        assert session.scalar(select(func.count(OutboxEvent.id))) == 1
    finally:
        main.app.dependency_overrides.clear()
        session.close()


def test_engine_session_uses_stored_assessment_and_finalizes_once(monkeypatch):
    client, session = _client(monkeypatch)
    try:
        client.post("/v1/assessments", json=_assessment_payload())
        started = client.post("/v1/sessions", json={"engine": "statistical", "assessment_id": 91})
        assert started.status_code == 201
        session_id = started.json()["session_id"]
        assert "correct_option_index" not in str(started.json()["state"])

        answered = client.post(
            f"/v1/sessions/{session_id}/submit", json={"answer": {"selected_option": 0}}
        )
        assert answered.status_code == 200
        first = client.post(f"/v1/sessions/{session_id}/finalize")
        second = client.post(f"/v1/sessions/{session_id}/finalize")
        assert first.status_code == 200
        assert first.json() == second.json()
        assert session.scalar(select(func.count(OutboxEvent.id))) == 1
    finally:
        main.app.dependency_overrides.clear()
        session.close()


def test_migrated_quiz_catalogue_delivery_and_submission(monkeypatch):
    client, session = _client(monkeypatch)
    try:
        quiz = GeneratedQuiz(
            id=12, user_id=99, title="Imported quiz", source_name="manual.pdf",
            source_type="pdf", difficulty="intermediate", generator="legacy",
        )
        quiz.questions = [GeneratedQuizQuestion(
            id=21, order=1, question_text="Choose A", options=["A", "B"],
            correct_option_index=0, explanation="A is correct", concept="sampling",
        )]
        session.add(quiz)
        session.commit()

        listing = client.get("/v1/quiz")
        assert listing.status_code == 200
        assert listing.json()[0]["question_count"] == 1
        delivered = client.get("/v1/quiz/12").json()
        assert "correct_index" not in delivered["questions"][0]

        result = client.post("/v1/quiz/12/submit", json={"answers": {"21": 0}})
        assert result.status_code == 200
        assert result.json()["score_percent"] == 100.0
        assert client.get("/v1/quiz/12/attempts").json()[0]["correct_count"] == 1
        assert client.delete("/v1/quiz/12").status_code == 403
    finally:
        main.app.dependency_overrides.clear()
        session.close()


def test_behavioural_case_catalogue_and_session(monkeypatch):
    client, session = _client(monkeypatch)
    try:
        cases = client.get("/v1/behavioural/cases")
        corpus = client.get("/v1/behavioural/corpus")
        assert cases.status_code == 200 and len(cases.json()) >= 1
        assert corpus.status_code == 200 and len(corpus.json()) >= 1
        case = cases.json()[0]

        started = client.post("/v1/behavioural/session/start", json={"case_id": case["id"]})
        assert started.status_code == 201
        session_id = started.json()["session_id"]
        question = started.json()["current_question"]
        submitted = client.post(
            f"/v1/behavioural/session/{session_id}/submit",
            json={"question_id": question["id"], "selected_option_id": "A"},
        )
        assert submitted.status_code == 200
        assert submitted.json()["session_completed"] is True
        summary = client.get(f"/v1/behavioural/session/{session_id}/summary")
        assert summary.status_code == 200
        assert summary.json()["procedural_compliance_score"] == 100.0
    finally:
        main.app.dependency_overrides.clear()
        session.close()


def test_interview_is_persisted_and_can_finish_after_session_reload(monkeypatch):
    client, session = _client(monkeypatch)

    async def interview_ai(_messages, schema, _authorization):
        if "reply" in schema:
            return ({
                "reply": "You mentioned transparent evidence. How would you explain a disputed result to a non-technical stakeholder?",
                "competencies_shown": ["Course Knowledge", "Communication"],
                "feedback": "You connected evidence with transparent communication.",
            }, "groq")
        return ({
            "competency_scores": {
                "Course Knowledge": {"score": 82, "evidence": "Used evidence explicitly.", "recommendation": "Add a workplace example."},
            },
            "overall_assessment": "The officer gave an evidence-led answer.",
            "strengths": ["Evidence-led reasoning"],
            "improvements": ["Add more operational detail"],
            "upskilling": ["Practise stakeholder briefings"],
        }, "groq")

    monkeypatch.setattr(main, "_interview_ai", interview_ai)
    async def interview_context(_course_id):
        return {"title":"Official Statistics","organization":"MoSPI","overview":"Official evidence","modules":["Evidence"],"material":"Published data and transparent decisions"}
    monkeypatch.setattr(main,"_interview_course_context",interview_context)
    try:
        started = client.post("/v1/behavioural/interview/start", json={
            "course_id": 11, "officer_name": "Test Learner", "target_duration_minutes": 30,
        })
        assert started.status_code == 201
        session_id = started.json()["session_id"]
        assert "Official Statistics" in started.json()["initial_ai_question"]

        answered = client.post("/v1/behavioural/interview/turn", headers={"Authorization": "Bearer test"}, json={
            "session_id": session_id,
            "officer_response": "I would use evidence, communicate the risks, and make a transparent decision.",
            "elapsed_seconds": 75,
            "input_mode": "typed",
        })
        assert answered.status_code == 200
        assert answered.json()["turns_completed"] == 1
        assert answered.json()["ai_provider"] == "groq"
        assert "non-technical stakeholder" in answered.json()["ai_question"]
        session.expire_all()  # Emulates loading state afresh after a process restart.
        stored = session.get(SessionRecord, session_id)
        assert stored.state["turns"][0]["elapsed_seconds"] == 75

        finished = client.post(f"/v1/behavioural/interview/{session_id}/end", headers={"Authorization": "Bearer test"})
        assert finished.status_code == 200
        assert finished.json()["total_turns"] == 1
        assert finished.json()["overall_assessment"] == "The officer gave an evidence-led answer."
        assert finished.json()["evaluation_method"].endswith("using groq.")
        assert client.post(f"/v1/behavioural/interview/{session_id}/end").json() == finished.json()
    finally:
        main.app.dependency_overrides.clear()
        session.close()


def test_dictation_endpoint_forwards_wav_to_speech_provider(monkeypatch):
    client, session = _client(monkeypatch)

    class ProviderResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"transcript": "This is my dictated answer.", "request_id": "speech-1"}

    class ProviderClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            return None

        async def post(self, *_, **kwargs):
            assert kwargs["files"]["file"][2] == "audio/wav"
            assert kwargs["headers"]["api-subscription-key"] == "test-key"
            return ProviderResponse()

    try:
        monkeypatch.setattr(main, "get_settings", lambda: SimpleNamespace(sarvam_api_key="test-key"))
        monkeypatch.setattr(main.httpx, "AsyncClient", lambda **_: ProviderClient())
        response = client.post(
            "/v1/behavioural/interview/transcribe",
            files={"audio": ("dictation.wav", b"RIFF" + b"0" * 2000, "audio/wav")},
        )
        assert response.status_code == 200
        assert response.json() == {"text": "This is my dictated answer.", "provider": "sarvam", "request_id": "speech-1"}
    finally:
        main.app.dependency_overrides.clear()
        session.close()


def test_digital_scenario_branches_and_survives_session_reload(monkeypatch):
    client, session = _client(monkeypatch)
    try:
        scenarios = client.get("/v1/digital-governance/scenarios")
        assert scenarios.status_code == 200
        assert len(scenarios.json()) == 5
        selected = scenarios.json()[0]
        started = client.post("/v1/digital-governance/scenarios/session/start", json={"scenario_id": selected["id"]})
        assert started.status_code == 200
        session_id = started.json()["session_id"]
        question = started.json()["current_question"]
        terminal_option = next(option for option in question["options"] if option["is_terminal"])
        answered = client.post(
            f"/v1/digital-governance/scenarios/session/{session_id}/answer",
            json={"option_id": terminal_option["option_id"]},
        )
        assert answered.status_code == 200
        assert answered.json()["is_terminal"] is True
        session.expire_all()
        summary = client.get(f"/v1/digital-governance/scenarios/session/{session_id}/summary")
        assert summary.status_code == 200
        assert summary.json() == answered.json()["session_summary"]
        assert summary.json()["decision_trail"][0]["selected_option_id"] == terminal_option["option_id"]
    finally:
        main.app.dependency_overrides.clear()
        session.close()


def test_authored_lab_catalogue_does_not_expose_hidden_tests_or_solution(monkeypatch):
    client, session = _client(monkeypatch)
    try:
        session.add(TechnicalLabTemplate(
            id="python-example",title="Example lab",skill="Python",language="python",difficulty="beginner",
            instructions_template="Implement {function_name} for {objective}",
            starter_code_template="def solve(value):\n    pass\n",solution_template="def solve(value): return value",
            tags=["python"],constraints=[],test_cases_template=[
                {"name":"public","test_code":"assert solve(1) == 1","is_hidden":False},
                {"name":"private","test_code":"assert solve(2) == 2","is_hidden":True},
            ],
        ))
        session.commit()
        listing=client.get("/v1/technical-courses/labs")
        assert listing.status_code==200 and listing.json()[0]["id"]==1001
        detail=client.get("/v1/technical-courses/labs/1001")
        assert detail.status_code==200
        assert len(detail.json()["test_cases"])==1
        assert "solution" not in detail.json()
        assert "solve" in detail.json()["instructions"]
    finally:
        main.app.dependency_overrides.clear()
        session.close()


def test_pasted_quiz_generation_persists_questions(monkeypatch):
    client, session = _client(monkeypatch)
    async def generated(_source,_count,_difficulty,_authorization,_ai_url):
        return ([{"question":"Which source is official?","options":["Published series","Rumour","Guess","Draft"],"correct_index":0,"explanation":"The published series is authoritative.","concept":"Source quality"}],"llm")
    monkeypatch.setattr(main,"generate_questions",generated)
    try:
        response=client.post("/v1/quiz/generate",data={"text":"Official statistics require validated published evidence. "*6,"num_questions":"1","difficulty":"beginner"})
        assert response.status_code==201
        quiz_id=response.json()["id"]
        assert response.json()["question_count"]==1
        assert response.json()["generator"]=="llm"
        assert client.get(f"/v1/quiz/{quiz_id}").status_code==200
    finally:
        main.app.dependency_overrides.clear()
        session.close()
