import json
from datetime import datetime, timezone
from typing import Any, Dict

import redis
import redis.asyncio as redis_async

from app.core.config import get_settings

settings = get_settings()


def event_channel(job_id: str) -> str:
    return f"job_progress:{job_id}"


def redis_client() -> redis.Redis:
    return redis.Redis.from_url(settings.redis_url, decode_responses=True)


def redis_async_client() -> redis_async.Redis:
    return redis_async.Redis.from_url(settings.redis_url, decode_responses=True)


def publish_event(
    job_id: str,
    status: str,
    progress: int,
    message: str,
    *,
    timestamp: str | None = None,
) -> None:
    event_timestamp = timestamp or datetime.now(timezone.utc).isoformat()
    payload: Dict[str, Any] = {
        "job_id": job_id,
        "status": status,
        "progress": progress,
        "message": message,
        "timestamp": event_timestamp,
    }
    client = redis_client()
    client.publish(event_channel(job_id), json.dumps(payload))
    client.close()
