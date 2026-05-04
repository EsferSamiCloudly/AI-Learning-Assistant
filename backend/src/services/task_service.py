from celery import Celery
from ..config import settings

celery_app = Celery(
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)


def dispatch_embed_document(
    document_id: str,
    file_bytes_b64: str,
    filename: str,
    user_id: str,
) -> str:
    task = celery_app.send_task(
        "embed_document",
        args=[document_id, file_bytes_b64, filename, user_id],
    )
    return task.id


def get_task_status(task_id: str) -> dict:
    result = celery_app.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.ready() else None,
    }