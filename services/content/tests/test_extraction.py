import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from igot_content import main, tasks
from igot_content.database import Base, Job, get_db
from igot_content.extraction import ExtractionError, discovery_links, extract_web_text, normalize_text


def test_normalize_and_discovery():
    assert normalize_text("a   b\n\n\n c") == "a b\n\n c"
    assert len(discovery_links("statistics")) == 3


def test_private_web_sources_are_rejected():
    with pytest.raises(ExtractionError, match="private or reserved"):
        asyncio.run(extract_web_text("http://127.0.0.1/private"))


def _client() -> tuple[TestClient, Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    ).execution_options(schema_translate_map={"content": None})
    Base.metadata.create_all(engine)
    session = Session(engine, expire_on_commit=False)

    def test_db():
        yield session

    main.app.dependency_overrides[get_db] = test_db
    main.app.dependency_overrides[main.principal] = lambda: main.Principal(7, "learner")
    return TestClient(main.app), session


def test_transcript_processing_persists_clean_chunks():
    client, session = _client()
    try:
        response = client.post(
            "/v1/technical-courses/process",
            json={
                "title": "Python",
                "course_id": 11,
                "raw_text": "WEBVTT\n\n00:00:00.000 --> 00:00:03.000\n[Music] Learn pandas data frames.",
                "metadata": {"source": "lecture.vtt"},
            },
        )
        assert response.status_code == 200
        assert response.json()["chunk_count"] == 1
        assert "WEBVTT" not in response.json()["chunks"][0]["text"]
    finally:
        main.app.dependency_overrides.clear()
        session.close()


def test_broker_failure_leaves_durable_queued_job(monkeypatch):
    client, session = _client()
    try:
        monkeypatch.setattr(tasks.process_source_job, "delay", lambda _: (_ for _ in ()).throw(RuntimeError("broker down")))
        source = client.post(
            "/v1/sources", json={"kind": "web", "uri": "https://example.com", "title": "Example"}
        ).json()
        response = client.post(f"/v1/sources/{source['id']}/process")
        assert response.status_code == 202
        assert response.json()["dispatched"] is False
        job = session.scalar(select(Job))
        assert job is not None and job.status == "queued"
    finally:
        main.app.dependency_overrides.clear()
        session.close()
