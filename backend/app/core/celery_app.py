from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery("document_worker", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    imports=("app.workers.tasks",),
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)
