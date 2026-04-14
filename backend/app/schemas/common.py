from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TimestampedSchema(BaseModel):
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    message: str


class UUIDResponse(BaseModel):
    id: UUID
