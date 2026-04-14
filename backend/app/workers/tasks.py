import re
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from celery.utils.log import get_task_logger
from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.enums import DocumentStatus, JobStatus
from app.core.events import publish_event
from app.models.document import Document
from app.models.extracted_result import ExtractedResult
from app.models.job import Job
from app.models.job_event import JobEvent

logger = get_task_logger(__name__)

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have", "he", "in",
    "is", "it", "its", "of", "on", "or", "that", "the", "to", "was", "were", "will", "with", "this",
    "these", "those", "we", "you", "your", "our", "their", "they", "i", "me", "my", "us", "but", "if",
    "then", "than", "also", "about", "into", "over", "under", "can", "could", "should", "would", "may",
    "made", "between", "corp", "ltd", "inc", "llc", "co", "company", "document",
}


def _update_job_and_publish(
    db: Session,
    *,
    job: Job,
    document: Document,
    stage_status: str,
    progress: int,
    message: str,
    job_status: JobStatus,
    document_status: DocumentStatus,
) -> None:
    event_time = datetime.now(timezone.utc)
    job.progress = progress
    job.status = job_status
    document.status = document_status

    event = JobEvent(
        job_id=job.id,
        status=stage_status,
        progress=progress,
        message=message,
        timestamp=event_time,
    )

    db.add(event)
    db.add_all([job, document])
    db.commit()
    publish_event(
        str(job.id),
        stage_status,
        progress,
        message,
        timestamp=event_time.isoformat(),
    )


def _read_text(document: Document) -> str:
    path = document.storage_path
    if not path:
        return ""

    try:
        with Path(path).open("r", encoding="utf-8") as src:
            return src.read()
    except UnicodeDecodeError:
        with Path(path).open("r", encoding="latin-1") as src:
            return src.read()
    except OSError:
        return ""


def _summary_lines(text: str) -> list[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    meaningful = [line for line in lines if len(re.findall(r"[A-Za-z0-9]+", line)) >= 3]
    selected = meaningful[:3] if meaningful else lines[:3]
    return selected


def _extract_keywords(text: str, filename: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z][A-Za-z'-]{2,}", text.lower())
    filtered = [token for token in tokens if token not in STOPWORDS]
    counts = Counter(filtered)
    keywords = [word for word, _ in counts.most_common(6)]

    if len(keywords) < 3:
        filename_tokens = re.findall(r"[A-Za-z][A-Za-z'-]{2,}", Path(filename).stem.lower())
        for token in filename_tokens:
            if token in STOPWORDS or token in keywords:
                continue
            keywords.append(token)
            if len(keywords) >= 3:
                break

    return keywords[:6]


def _derive_title(lines: list[str], keywords: list[str], filename: str) -> str:
    if lines:
        return lines[0].strip().title()[:255]
    if keywords:
        return " ".join(word.title() for word in keywords[:5])[:255]
    return Path(filename).stem.replace("_", " ").replace("-", " ").title()[:255] or "Untitled Document"


def _derive_category(text: str, filename: str) -> str:
    lower = f"{text} {filename}".lower()
    if "invoice" in lower or "payment" in lower:
        return "Finance"
    if "contract" in lower or "agreement" in lower:
        return "Finance"
    if "patient" in lower or "medical" in lower:
        return "Healthcare"
    return "General"


def _extract_structured(document: Document) -> dict:
    text = _read_text(document)
    lines = _summary_lines(text)
    keywords = _extract_keywords(text, document.filename)
    first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
    title = first_line.title()[:255] if first_line else _derive_title(lines, keywords, document.filename)
    category = _derive_category(text, document.filename)
    summary = " ".join(lines)
    summary = summary.replace("\n", " ").strip()

    if not summary:
        summary = title

    return {
        "title": title,
        "category": category,
        "summary": summary,
        "keywords": keywords,
        "file_size": document.size,
        "processed_at": datetime.now(timezone.utc),
    }


@celery_app.task(bind=True, max_retries=2, default_retry_delay=3)
def process_document_task(self, document_id: str, job_id: str) -> None:
    db: Session = SessionLocal()
    try:
        document = db.get(Document, UUID(document_id))
        job = db.get(Job, UUID(job_id))

        if not document or not job:
            logger.error("Missing document/job for processing: %s %s", document_id, job_id)
            return

        # Stage 1: queued
        _update_job_and_publish(
            db,
            job=job,
            document=document,
            stage_status="job_queued",
            progress=0,
            message="Job queued",
            job_status=JobStatus.queued,
            document_status=DocumentStatus.queued,
        )

        time.sleep(1)

        # Stage 2: started
        _update_job_and_publish(
            db,
            job=job,
            document=document,
            stage_status="job_started",
            progress=5,
            message="Worker started processing",
            job_status=JobStatus.processing,
            document_status=DocumentStatus.processing,
        )

        # Stage 3: parsing start
        _update_job_and_publish(
            db,
            job=job,
            document=document,
            stage_status="document_parsing_started",
            progress=10,
            message="Document parsing started",
            job_status=JobStatus.processing,
            document_status=DocumentStatus.processing,
        )
        time.sleep(2)

        # Stage 4: parsing complete
        _update_job_and_publish(
            db,
            job=job,
            document=document,
            stage_status="document_parsing_completed",
            progress=30,
            message="Document parsing completed",
            job_status=JobStatus.processing,
            document_status=DocumentStatus.processing,
        )

        # Stage 5: extraction start
        _update_job_and_publish(
            db,
            job=job,
            document=document,
            stage_status="field_extraction_started",
            progress=60,
            message="Field extraction started",
            job_status=JobStatus.processing,
            document_status=DocumentStatus.processing,
        )
        time.sleep(2)

        # Stage 6: extraction complete
        extracted = _extract_structured(document)
        _update_job_and_publish(
            db,
            job=job,
            document=document,
            stage_status="field_extraction_completed",
            progress=90,
            message="Field extraction completed",
            job_status=JobStatus.processing,
            document_status=DocumentStatus.processing,
        )

        result = db.query(ExtractedResult).filter(ExtractedResult.document_id == document.id).one_or_none()
        if result is None:
            result = ExtractedResult(document_id=document.id)
        result.title = extracted["title"]
        result.category = extracted["category"]
        result.summary = extracted["summary"]
        result.keywords = extracted["keywords"]
        result.file_size = extracted["file_size"]
        result.processed_at = extracted["processed_at"]
        db.add(result)
        db.commit()

        # Stage 7: result stored
        _update_job_and_publish(
            db,
            job=job,
            document=document,
            stage_status="final_result_stored",
            progress=95,
            message="Final extracted result stored",
            job_status=JobStatus.processing,
            document_status=DocumentStatus.processing,
        )

        time.sleep(1)

        # Stage 8: complete
        _update_job_and_publish(
            db,
            job=job,
            document=document,
            stage_status="job_completed",
            progress=100,
            message="Job completed successfully",
            job_status=JobStatus.completed,
            document_status=DocumentStatus.completed,
        )

    except Exception as exc:  # noqa: BLE001
        db.rollback()
        document = db.get(Document, UUID(document_id))
        job = db.get(Job, UUID(job_id))

        if self.request.retries < self.max_retries:
            retry_event_time = datetime.now(timezone.utc)
            if job:
                db.add(
                    JobEvent(
                        job_id=job.id,
                        status="job_retrying",
                        progress=job.progress,
                        message=f"Retrying job after error: {exc}",
                        timestamp=retry_event_time,
                    )
                )
                db.commit()
            publish_event(
                job_id,
                "job_retrying",
                job.progress if job else 0,
                f"Retrying job after error: {exc}",
                timestamp=retry_event_time.isoformat(),
            )
            raise self.retry(exc=exc)

        if job:
            job.status = JobStatus.failed
            job.error_message = str(exc)
            db.add(job)
        if document:
            document.status = DocumentStatus.failed
            db.add(document)
        db.commit()

        failed_event_time = datetime.now(timezone.utc)
        if job:
            db.add(
                JobEvent(
                    job_id=job.id,
                    status="job_failed",
                    progress=job.progress,
                    message=f"Job failed: {exc}",
                    timestamp=failed_event_time,
                )
            )
            db.commit()
        publish_event(
            job_id,
            "job_failed",
            job.progress if job else 0,
            f"Job failed: {exc}",
            timestamp=failed_event_time.isoformat(),
        )
        logger.exception("Job failed after retries: %s", job_id)
    finally:
        db.close()
