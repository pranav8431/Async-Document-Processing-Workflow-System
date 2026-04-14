from app.models.document import Document
from app.schemas.document import DocumentDetail, DocumentRead, ExtractedResultRead, JobRead
from app.services.document_service import latest_job


def serialize_document(doc: Document) -> DocumentRead:
    job = latest_job(doc)
    return DocumentRead(
        id=doc.id,
        filename=doc.filename,
        file_type=doc.file_type,
        size=doc.size,
        status=doc.status,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        latest_job=JobRead.model_validate(job) if job else None,
    )


def serialize_document_detail(doc: Document) -> DocumentDetail:
    base = serialize_document(doc)
    return DocumentDetail(
        **base.model_dump(),
        extracted_result=ExtractedResultRead.model_validate(doc.extracted_result) if doc.extracted_result else None,
    )
