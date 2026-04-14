from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.core.enums import DocumentStatus, JobStatus


class ExtractedResultBase(BaseModel):
    title: str
    category: str
    summary: str
    keywords: list[str]
    file_size: Optional[int] = None
    processed_at: Optional[datetime] = None
    finalized: bool


class ExtractedResultUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    summary: Optional[str] = None
    keywords: Optional[list[str]] = None


class ExtractedResultRead(ExtractedResultBase):
    id: int
    document_id: UUID

    model_config = ConfigDict(from_attributes=True)


class JobRead(BaseModel):
    id: UUID
    document_id: UUID
    status: JobStatus
    progress: int
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentRead(BaseModel):
    id: UUID
    filename: str
    file_type: str
    size: int
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime
    latest_job: Optional[JobRead] = None

    model_config = ConfigDict(from_attributes=True)


class DocumentDetail(DocumentRead):
    extracted_result: Optional[ExtractedResultRead] = None
