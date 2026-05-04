from pydantic import BaseModel
from datetime import datetime


class DocumentUploadResponse(BaseModel):
    id: str
    filename: str
    embed_status: str
    celery_task_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    id: str
    filename: str
    embed_status: str
    page_count: int | None
    created_at: datetime

    class Config:
        from_attributes = True