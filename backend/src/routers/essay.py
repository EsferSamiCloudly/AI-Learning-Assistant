from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from ..database import get_db
from ..dependencies import get_current_user
from ..models.db.user import User
from ..models.db.outputs import EssayOutput
from ..models.schemas.essay import EssayRequest, EssayResponse
from ..services import mcp_client

router = APIRouter()


@router.post("/generate", response_model=EssayResponse)
async def generate_essay(
    body: EssayRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    content = await mcp_client.call_essay_writer(
        topic=body.topic,
        tone=body.tone,
        length=body.length,
        include_outline=body.include_outline,
    )

    essay = EssayOutput(
        user_id=current_user.id,
        topic=body.topic,
        tone=body.tone,
        length=body.length,
        content=content,
    )
    db.add(essay)
    await db.flush()
    await db.refresh(essay)

    return EssayResponse(id=str(essay.id), topic=essay.topic, content=essay.content)


@router.get("/history", response_model=list[EssayResponse])
async def get_essay_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(EssayOutput)
        .where(EssayOutput.user_id == current_user.id)
        .order_by(EssayOutput.created_at.desc())
    )
    essays = result.scalars().all()
    return [
        EssayResponse(id=str(e.id), topic=e.topic, content=e.content)
        for e in essays
    ]


@router.get("/history/{essay_id}", response_model=EssayResponse)
async def get_essay(
    essay_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(EssayOutput).where(
            EssayOutput.id == uuid.UUID(essay_id),
            EssayOutput.user_id == current_user.id,
        )
    )
    essay = result.scalar_one_or_none()
    if not essay:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Essay not found")
    return EssayResponse(id=str(essay.id), topic=essay.topic, content=essay.content)


@router.delete("/history/{essay_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_essay(
    essay_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(EssayOutput).where(
            EssayOutput.id == uuid.UUID(essay_id),
            EssayOutput.user_id == current_user.id,
        )
    )
    essay = result.scalar_one_or_none()
    if not essay:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Essay not found")
    await db.delete(essay)