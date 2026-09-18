from datetime import datetime,timezone
from celery import Celery
from sqlalchemy import select
from .config import get_settings
from .database import LabSession,SessionLocal
from .runtime import DockerRuntime
celery=Celery("labs",broker=get_settings().rabbitmq_url)
@celery.task(name="labs.cleanup_expired")
def cleanup_expired():
    with SessionLocal() as db:
        records=db.scalars(select(LabSession).where(LabSession.status.in_(["running","provisioning"]),LabSession.expires_at<datetime.now(timezone.utc))).all()
        runtime=DockerRuntime()
        for record in records:
            runtime.terminate(record.workspace_container_id,record.target_container_ids,record.network_id);record.status="expired"
        db.commit();return len(records)
