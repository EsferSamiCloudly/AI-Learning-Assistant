from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
import uuid

from ..database import get_db
from ..dependencies import get_current_user
from ..models.db.user import User
from ..models.db.document import Document
from ..models.db.outputs import QuestionSet
from ..models.schemas.questions import GenerateQuestionsRequest, QuestionsResponse, Question
from ..services import mcp_client

router = APIRouter()


@router.post("/generate", response_model=QuestionsResponse)
async def generate_questions(
    body: GenerateQuestionsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not body.content and not body.document_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either content or document_id must be provided",
        )

    content = body.content

    if body.document_id:
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
                detail=f"Document not ready. Status: {doc.embed_status}",
            )

        chunks_result = await db.execute(
            text("SELECT content FROM vectors.document_chunks WHERE document_id = :doc_id ORDER BY chunk_index"),
            {"doc_id": body.document_id},
        )
        chunks = chunks_result.fetchall()
        content = "\n".join([row[0] for row in chunks])

    questions = await mcp_client.call_question_generator(
        content=content,
        difficulty=body.difficulty,
        count=body.count,
        domain=body.domain if not body.document_id else None,
    )

    question_set = QuestionSet(
        user_id=current_user.id,
        difficulty=body.difficulty,
        domain=body.domain if not body.document_id else None,
        count=len(questions),
        questions=questions,
        source_text=content[:500] if content else None,
    )
    db.add(question_set)
    await db.flush()
    await db.refresh(question_set)

    return QuestionsResponse(
        id=str(question_set.id),
        questions=[Question(**q) for q in questions],
        difficulty=question_set.difficulty,
        count=question_set.count,
    )


@router.get("/history", response_model=list[QuestionsResponse])
async def get_questions_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(QuestionSet)
        .where(QuestionSet.user_id == current_user.id)
        .order_by(QuestionSet.created_at.desc())
    )
    items = result.scalars().all()
    return [
        QuestionsResponse(
            id=str(q.id),
            questions=[Question(**item) for item in q.questions],
            difficulty=q.difficulty,
            count=q.count,
        )
        for q in items
    ]


@router.get("/history/{set_id}", response_model=QuestionsResponse)
async def get_question_set(
    set_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(QuestionSet).where(
            QuestionSet.id == uuid.UUID(set_id),
            QuestionSet.user_id == current_user.id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question set not found")
    return QuestionsResponse(
        id=str(item.id),
        questions=[Question(**q) for q in item.questions],
        difficulty=item.difficulty,
        count=item.count,
    )


@router.delete("/history/{set_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question_set(
    set_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(QuestionSet).where(
            QuestionSet.id == uuid.UUID(set_id),
            QuestionSet.user_id == current_user.id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question set not found")
    await db.delete(item)