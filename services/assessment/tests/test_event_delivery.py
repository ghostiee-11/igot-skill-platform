from contextlib import contextmanager
from datetime import datetime, timezone
from types import SimpleNamespace

import httpx
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from igot_assessment import dispatch_events
from igot_assessment.database import Base, OutboxEvent


def test_failed_delivery_remains_pending_and_retry_uses_same_event(monkeypatch):
    engine = create_engine("sqlite://").execution_options(schema_translate_map={"assessment": None})
    Base.metadata.create_all(engine)

    @contextmanager
    def session_factory():
        with Session(engine) as session:
            yield session

    monkeypatch.setattr(dispatch_events, "SessionLocal", session_factory)
    payload = {"event_id": "stable-event", "occurred_at": datetime.now(timezone.utc).isoformat(),
               "user_id": 7, "course_id": 11, "attempt_id": "uuid-attempt", "score_percent": 100,
               "passed": True, "evidence": [{"competency_code": "statistical_price_statistics",
               "domain_code": "statistical", "level": 5, "source_type": "assessment", "source_id": "uuid-attempt"}]}
    with session_factory() as db:
        db.add(OutboxEvent(topic="assessment.completed.v1", payload=payload))
        db.commit()
    calls = []
    fail = True

    def handler(request):
        import json
        calls.append((request.url.path, json.loads(request.content)))
        assert request.headers["X-Internal-Secret"] == "test-secret"
        if fail and request.url.path.endswith("batch"):
            return httpx.Response(503)
        return httpx.Response(200, json={"status": "accepted"})

    settings = SimpleNamespace(learning_url="http://learning", competency_url="http://competency",
                               internal_event_secret="test-secret")
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        assert dispatch_events.dispatch_once(client, settings) == 0
        with session_factory() as db:
            assert db.scalar(select(OutboxEvent)).published_at is None
        fail = False
        assert dispatch_events.dispatch_once(client, settings) == 1
        assert dispatch_events.dispatch_once(client, settings) == 0
    assert len(calls) == 4
    assert calls[0][1]["event_id"] == calls[2][1]["event_id"] == "stable-event"
    assert calls[3][1]["evidence"][0]["observed_at"] == payload["occurred_at"]
