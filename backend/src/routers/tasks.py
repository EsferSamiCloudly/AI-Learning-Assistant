import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..dependencies import get_current_user
from ..models.db.user import User
from ..models.db.document import Document
from ..models.schemas.task import TaskStatusResponse

router = APIRouter()

@router.get("/{task_id}", response_model=TaskStatusResponse)
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Document).where(Document.id == uuid.UUID(task_id))
    )
    doc = result.scalar_one_or_none()

    if not doc:
        return TaskStatusResponse(task_id=task_id, status="PENDING", result=None)

    status_map = {
        "pending": "PENDING",
        "processing": "STARTED",
        "done": "SUCCESS",
        "failed": "FAILURE",
    }

    return TaskStatusResponse(
        task_id=task_id,
        status=status_map.get(doc.embed_status, "PENDING"),
        result=None,
    )