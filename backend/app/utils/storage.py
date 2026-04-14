import os
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import get_settings

settings = get_settings()


def ensure_upload_dir() -> Path:
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def persist_upload(file: UploadFile) -> str:
    upload_dir = ensure_upload_dir()
    suffix = Path(file.filename or "").suffix
    saved_name = f"{uuid.uuid4()}{suffix}"
    target = upload_dir / saved_name

    with target.open("wb") as out_file:
        out_file.write(file.file.read())

    return str(target)
