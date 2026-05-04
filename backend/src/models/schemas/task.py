from pydantic import BaseModel
from typing import Any


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Any | None = None