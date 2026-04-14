from fastapi import FastAPI
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.documents import router as documents_router
from app.api.jobs import router as jobs_router
from app.api.upload import router as upload_router
from app.core.config import get_settings
from app.core.database import Base, engine
from app.core.events import event_channel, redis_async_client
from app.utils.storage import ensure_upload_dir

settings = get_settings()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router, prefix=settings.api_prefix)
app.include_router(documents_router, prefix=settings.api_prefix)
app.include_router(jobs_router, prefix=settings.api_prefix)


@app.on_event("startup")
def on_startup() -> None:
    ensure_upload_dir()
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS storage_path VARCHAR(1024)"))
        conn.execute(text("ALTER TABLE extracted_results ADD COLUMN IF NOT EXISTS file_size INTEGER"))
        conn.execute(text("ALTER TABLE extracted_results ADD COLUMN IF NOT EXISTS processed_at TIMESTAMPTZ"))


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.websocket("/ws/jobs/{job_id}")
async def job_progress_ws(websocket: WebSocket, job_id: str):
    await websocket.accept()
    channel = event_channel(job_id)
    client = redis_async_client()
    pubsub = client.pubsub()
    await pubsub.subscribe(channel)

    try:
        async for message in pubsub.listen():
            if message.get("type") != "message":
                continue
            payload = message.get("data")
            if payload is None:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            await websocket.send_text(payload)
    except WebSocketDisconnect:
        return
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()
        await client.close()
