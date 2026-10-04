"""Retry assessment outbox delivery through service-owned idempotent HTTP APIs."""
import logging
import time
from datetime import datetime, timezone

import httpx
from sqlalchemy import select

from .config import get_settings
from .database import OutboxEvent, SessionLocal

logger = logging.getLogger(__name__)


def deliver(client, payload, settings):
    headers = {"X-Internal-Secret": settings.internal_event_secret}
    if payload.get("course_id") is not None:
        result = client.post(f"{settings.learning_url}/v1/internal/events/assessment-completed",
                             json=payload, headers=headers)
        result.raise_for_status()
    evidence = []
    for item in payload.get("evidence", []):
        evidence.append({**item, "event_id": payload["event_id"], "user_id": payload["user_id"],
                         "observed_at": payload["occurred_at"]})
    if evidence:
        result = client.post(f"{settings.competency_url}/v1/evidence/batch", json={"evidence": evidence}, headers=headers)
        result.raise_for_status()


def dispatch_once(client, settings):
    count = 0
    with SessionLocal() as db:
        events = db.scalars(select(OutboxEvent).where(OutboxEvent.published_at.is_(None))
                            .order_by(OutboxEvent.occurred_at).limit(50).with_for_update(skip_locked=True)).all()
        for event in events:
            try:
                deliver(client, event.payload, settings)
            except httpx.HTTPError as exc:
                logger.warning("Assessment event %s pending: %s", event.id, exc)
                continue
            event.published_at = datetime.now(timezone.utc)
            count += 1
        db.commit()
    return count


def main():
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    with httpx.Client(timeout=10) as client:
        while True:
            try:
                count = dispatch_once(client, settings)
                if count:
                    logger.info("Delivered %s assessment events", count)
            except Exception:
                logger.exception("Assessment event dispatcher will retry")
            time.sleep(2)


if __name__ == "__main__":
    main()
