from celery import Celery
from .config import get_settings
from .database import Job,SessionLocal,Source
from .extraction import extract_web_text
from .storage import storage
celery=Celery("content",broker=get_settings().rabbitmq_url)
# RabbitMQ 4 rejects transient, non-exclusive control/event queues. Task queues
# stay durable; only worker-local control and event subscriptions are exclusive.
celery.conf.update(control_queue_exclusive=True, event_queue_exclusive=True)
@celery.task(name="content.process_source")
def process_source_job(job_id:str):
    import asyncio
    with SessionLocal() as db:
        job=db.get(Job,job_id)
        if not job or job.status=="completed":return
        source=db.get(Source,job.source_id);job.status="running";job.progress=10;source.status="processing";db.commit()
        try:
            if source.kind!="web":raise ValueError("binary document extraction requires an uploaded artifact")
            value,meta=asyncio.run(extract_web_text(source.uri));uri=storage().put(f"{source.id}/extracted.txt",value.encode())
            source.extracted_text=value;source.artifact_uri=uri;source.metadata_json={**source.metadata_json,**meta};source.status="ready";job.status="completed";job.progress=100;job.result={"artifact_uri":uri,"characters":len(value)}
        except Exception as exc:source.status="failed";job.status="failed";job.error=f"{type(exc).__name__}: {exc}"
        db.commit()
