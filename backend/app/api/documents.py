from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_db_dep
from app.api.serializers import serialize_document, serialize_document_detail
from app.core.enums import DocumentStatus
from app.schemas.common import MessageResponse
from app.schemas.document import DocumentDetail, DocumentRead, ExtractedResultUpdate
from app.services.document_service import (
    delete_document,
    export_document,
    finalize_document,
    get_document_detail,
    list_documents,
    update_extracted_fields,
)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=list[DocumentRead])
def get_documents(
    db: Session = Depends(get_db_dep),
    search: Optional[str] = Query(default=None),
    status: Optional[DocumentStatus] = Query(default=None),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
):
    documents = list_documents(db, search=search, status=status, sort_by=sort_by, sort_order=sort_order)
    return [serialize_document(document) for document in documents]


@router.get("/{document_id}")
def get_document(document_id: UUID, db: Session = Depends(get_db_dep)) -> DocumentDetail:
    document = get_document_detail(db, document_id)
    return serialize_document_detail(document)


@router.put("/{document_id}")
def update_document(
    document_id: UUID,
    payload: ExtractedResultUpdate,
    db: Session = Depends(get_db_dep),
) -> DocumentDetail:
    updated = update_extracted_fields(db, document_id, payload)
    return serialize_document_detail(updated)


@router.post("/{document_id}/finalize")
def finalize(document_id: UUID, db: Session = Depends(get_db_dep)) -> DocumentDetail:
    updated = finalize_document(db, document_id)
    return serialize_document_detail(updated)


@router.delete("/{document_id}", response_model=MessageResponse)
def delete(document_id: UUID, db: Session = Depends(get_db_dep)) -> MessageResponse:
    delete_document(db, document_id)
    return MessageResponse(message="Document deleted successfully")


@router.get("/{document_id}/export")
def export(document_id: UUID, format: str = Query(..., pattern="^(json|csv)$"), db: Session = Depends(get_db_dep)):
    document = get_document_detail(db, document_id)
    media_type, body, filename = export_document(document, format)
    return Response(
        content=body,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
