import csv
import io
from pathlib import Path
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import asc, desc, select
from sqlalchemy.orm import Session, selectinload

from app.core.enums import DocumentStatus
from app.models.document import Document
from app.models.extracted_result import ExtractedResult
from app.models.job import Job
from app.schemas.document import ExtractedResultUpdate


def list_documents(
    db: Session,
    search: Optional[str] = None,
    status: Optional[DocumentStatus] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> list[Document]:
    query = select(Document).options(selectinload(Document.jobs)).order_by(desc(Document.created_at))

    if search:
        query = query.where(Document.filename.ilike(f"%{search}%"))
    if status:
        query = query.where(Document.status == status)

    sortable_fields = {
        "filename": Document.filename,
        "size": Document.size,
        "created_at": Document.created_at,
        "updated_at": Document.updated_at,
        "status": Document.status,
    }
    sort_col = sortable_fields.get(sort_by, Document.created_at)
    query = query.order_by(asc(sort_col) if sort_order == "asc" else desc(sort_col))

    return list(db.execute(query).scalars().all())


def get_document_or_404(db: Session, document_id: UUID) -> Document:
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


def get_document_detail(db: Session, document_id: UUID) -> Document:
    query = (
        select(Document)
        .where(Document.id == document_id)
        .options(selectinload(Document.jobs), selectinload(Document.extracted_result))
    )
    document = db.execute(query).scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


def update_extracted_fields(db: Session, document_id: UUID, payload: ExtractedResultUpdate) -> Document:
    document = get_document_detail(db, document_id)
    if not document.extracted_result:
        document.extracted_result = ExtractedResult(document_id=document.id)

    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(document.extracted_result, key, value)

    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def finalize_document(db: Session, document_id: UUID) -> Document:
    document = get_document_detail(db, document_id)
    if not document.extracted_result:
        raise HTTPException(status_code=400, detail="No extracted result found")

    document.extracted_result.finalized = True
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def delete_document(db: Session, document_id: UUID) -> None:
    document = get_document_detail(db, document_id)

    if document.status == DocumentStatus.processing:
        raise HTTPException(status_code=409, detail="Cannot delete a document while processing")

    storage_path = document.storage_path
    db.delete(document)
    db.commit()

    if storage_path:
        try:
            Path(storage_path).unlink(missing_ok=True)
        except OSError:
            # Deletion from DB has already succeeded; file cleanup is best-effort.
            pass


def export_document(document: Document, fmt: str) -> tuple[str, bytes, str]:
    if not document.extracted_result:
        raise HTTPException(status_code=400, detail="No extracted result available")

    result = document.extracted_result
    data = {
        "document_id": str(document.id),
        "filename": document.filename,
        "status": document.status.value,
        "title": result.title,
        "category": result.category,
        "summary": result.summary,
        "keywords": result.keywords,
        "file_size": result.file_size,
        "processed_at": result.processed_at.isoformat() if result.processed_at else None,
        "finalized": result.finalized,
    }

    if fmt == "json":
        import json

        body = json.dumps(data, indent=2).encode("utf-8")
        return "application/json", body, f"{document.id}.json"

    if fmt == "csv":
        out = io.StringIO()
        writer = csv.DictWriter(out, fieldnames=list(data.keys()))
        writer.writeheader()
        writer.writerow({**data, "keywords": ";".join(data["keywords"])})
        body = out.getvalue().encode("utf-8")
        return "text/csv", body, f"{document.id}.csv"

    raise HTTPException(status_code=400, detail="Unsupported export format")


def latest_job(document: Document) -> Optional[Job]:
    if not document.jobs:
        return None
    return sorted(document.jobs, key=lambda item: item.created_at, reverse=True)[0]


