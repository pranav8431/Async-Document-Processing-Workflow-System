import asyncio
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db_dep
from app.core.enums import DocumentStatus, JobStatus
from app.core.events import event_channel, redis_client
from app.schemas.job import JobEventResponse, JobProgressResponse
from app.services.job_service import create_job, get_job_or_404, validate_retryable
from app.models.job_event import JobEvent
from app.workers.tasks import process_document_task

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}/progress", response_model=JobProgressResponse)
def get_progress(job_id: UUID, db: Session = Depends(get_db_dep)):
    job = get_job_or_404(db, job_id)
    return job


@router.get("/{job_id}/events", response_model=list[JobEventResponse])
def get_job_events(job_id: UUID, db: Session = Depends(get_db_dep)):
    get_job_or_404(db, job_id)
    events = (
        db.query(JobEvent)
        .filter(JobEvent.job_id == job_id)
        .order_by(JobEvent.timestamp.asc(), JobEvent.id.asc())
        .all()
    )
    return events


@router.get("/{job_id}/progress/stream")
async def stream_progress(job_id: UUID):
    channel = event_channel(str(job_id))

    async def event_generator():
        client = redis_client()
        pubsub = client.pubsub()
        pubsub.subscribe(channel)

        try:
            while True:
                message = pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message.get("data"):
                    payload = message["data"]
                    if isinstance(payload, bytes):
                        payload = payload.decode("utf-8")
                    yield f"data: {payload}\n\n"
                await asyncio.sleep(0.5)
        finally:
            pubsub.unsubscribe(channel)
            pubsub.close()
            client.close()

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/{job_id}/retry", response_model=JobProgressResponse)
def retry_job(job_id: UUID, db: Session = Depends(get_db_dep)):
    job = get_job_or_404(db, job_id)
    validate_retryable(job)

    new_job = create_job(db, job.document, status=JobStatus.queued)
    job.document.status = DocumentStatus.queued
    db.commit()
    db.refresh(new_job)

    process_document_task.delay(str(job.document_id), str(new_job.id))
    return new_job
