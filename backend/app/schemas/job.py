from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.core.enums import JobStatus


class JobProgressResponse(BaseModel):
    id: UUID
    status: JobStatus
    progress: int
    error_message: Optional[str]
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobEventResponse(BaseModel):
    id: int
    job_id: UUID
    status: str
    progress: int
    message: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
