import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func

from ..database import get_db
from ..dependencies import get_current_user
from ..models.db.user import User
from ..models.db.chat import ChatSession, ChatMessage
from ..models.db.document import Document
from ..models.schemas.chat import (
    CreateSessionRequest,
    SendMessageRequest,
    MessageResponse,
    SessionResponse,
    SessionDetailResponse,
)
from ..services import mcp_client

router = APIRouter()


@router.get("/sessions", response_model=list[SessionResponse])
async def get_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.updated_at.desc())
    )
    sessions = result.scalars().all()
    return [
        SessionResponse(
            id=str(s.id),
            title=s.title,
            mode=s.mode,
            document_id=str(s.document_id) if s.document_id else None,
            created_at=s.created_at,
            updated_at=s.updated_at,
        )
        for s in sessions
    ]


@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    body: CreateSessionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = None
    if body.mode == "pdf":
        if not body.document_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="document_id is required for PDF mode",
            )
        doc_result = await db.execute(
            select(Document).where(
                Document.id == uuid.UUID(body.document_id),
                Document.user_id == current_user.id,
            )
        )
        doc = doc_result.scalar_one_or_none()
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        if doc.embed_status != "done":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Document is not ready yet. Status: {doc.embed_status}",
            )

    session = ChatSession(
        user_id=current_user.id,
        mode=body.mode,
        document_id=uuid.UUID(body.document_id) if body.document_id else None,
        # Set title to filename for PDF sessions so user sees which doc they're chatting with
        title=doc.filename if doc else None,
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)

    return SessionResponse(
        id=str(session.id),
        title=session.title,
        mode=session.mode,
        document_id=str(session.document_id) if session.document_id else None,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ChatSession).where(ChatSession.id == uuid.UUID(session_id))
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    messages_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at.asc())
    )
    messages = messages_result.scalars().all()

    return SessionDetailResponse(
        session=SessionResponse(
            id=str(session.id),
            title=session.title,
            mode=session.mode,
            document_id=str(session.document_id) if session.document_id else None,
            created_at=session.created_at,
            updated_at=session.updated_at,
        ),
        messages=[
            MessageResponse(
                id=str(m.id),
                role=m.role,
                content=m.content,
                created_at=m.created_at,
            )
            for m in messages
        ],
    )


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ChatSession).where(ChatSession.id == uuid.UUID(session_id))
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    await db.execute(delete(ChatSession).where(ChatSession.id == session.id))


@router.post("/sessions/{session_id}/message", response_model=MessageResponse)
async def send_message(
    session_id: str,
    body: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ChatSession).where(ChatSession.id == uuid.UUID(session_id))
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # For general mode only — set title from first message
    # PDF sessions already have filename as title
    if not session.title:
        session.title = body.content[:60]
        db.add(session)

    # Save user message
    user_message = ChatMessage(
        session_id=session.id,
        role="user",
        content=body.content,
    )
    db.add(user_message)
    await db.flush()

    # Load last 10 messages for history
    history_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(10)
    )
    history = history_result.scalars().all()
    history.reverse()
    message_history = [{"role": m.role, "content": m.content} for m in history]

    # Call MCP server
    answer = await mcp_client.call_chatbot(
        question=body.content,
        session_id=session_id,
        user_id=str(current_user.id),
        mode=session.mode,
        document_id=str(session.document_id) if session.document_id else None,
        message_history=message_history,
    )

    # Save assistant message
    assistant_message = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=answer,
    )
    db.add(assistant_message)
    await db.flush()
    await db.refresh(assistant_message)

    # Update session updated_at
    session.updated_at = func.now()
    db.add(session)

    return MessageResponse(
        id=str(assistant_message.id),
        role=assistant_message.role,
        content=assistant_message.content,
        created_at=assistant_message.created_at,
    )