from pydantic import BaseModel
from datetime import datetime


class CreateSessionRequest(BaseModel):
    document_id: str | None = None
    mode: str = "general"


class SendMessageRequest(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class SessionResponse(BaseModel):
    id: str
    title: str | None
    mode: str
    document_id: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SessionDetailResponse(BaseModel):
    session: SessionResponse
    messages: list[MessageResponse]