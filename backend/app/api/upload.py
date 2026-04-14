from pathlib import Path
from typing import Annotated, List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_db_dep
from app.api.serializers import serialize_document
from app.core.enums import DocumentStatus, JobStatus
from app.models.document import Document
from app.schemas.document import DocumentRead
from app.services.job_service import create_job
from app.utils.storage import persist_upload
from app.workers.tasks import process_document_task

router = APIRouter(tags=["upload"])


@router.post("/upload", response_model=list[DocumentRead])
def upload_documents(files: Annotated[List[UploadFile], File(...)], db: Session = Depends(get_db_dep)):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    created_documents = []
    for file in files:
        file_path = persist_upload(file)
        stat = Path(file_path).stat()

        document = Document(
            filename=file.filename or Path(file_path).name,
            storage_path=file_path,
            file_type=(file.content_type or Path(file_path).suffix or "unknown")[:50],
            size=stat.st_size,
            status=DocumentStatus.queued,
        )
        db.add(document)
        db.flush()

        job = create_job(db, document, status=JobStatus.queued)
        created_documents.append((document, job))

    db.commit()

    for document, job in created_documents:
        process_document_task.delay(str(document.id), str(job.id))

    return [serialize_document(document) for document, _ in created_documents]
