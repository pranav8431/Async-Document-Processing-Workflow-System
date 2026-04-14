from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.enums import JobStatus
from app.models.document import Document
from app.models.job import Job


def create_job(db: Session, document: Document, status: JobStatus = JobStatus.queued) -> Job:
    job = Job(document_id=document.id, status=status, progress=0)
    db.add(job)
    db.flush()
    return job


def get_job_or_404(db: Session, job_id: UUID) -> Job:
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


def validate_retryable(job: Job) -> None:
    if job.status != JobStatus.failed:
        raise HTTPException(status_code=400, detail="Only failed jobs can be retried")
