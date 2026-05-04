from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
import uuid

from ..database import get_db
from ..dependencies import get_current_user
from ..models.db.user import User
from ..models.db.document import Document
from ..models.db.outputs import EvaluationResult
from ..models.schemas.evaluate import EvaluateRequest, EvaluateResponse, AnswerResult
from ..services import mcp_client

router = APIRouter()


@router.post("/answers", response_model=EvaluateResponse)
async def evaluate_answers(
    body: EvaluateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reference_content = body.reference_content

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
        reference_content = "\n".join([row[0] for row in chunks])

    pairs = [p.model_dump() for p in body.pairs]

    result = await mcp_client.call_answer_evaluator(
        pairs=pairs,
        reference_content=reference_content,
        mode=body.mode,
    )

    evaluation = EvaluationResult(
        user_id=current_user.id,
        mode=body.mode,
        results=result["results"],
        total_score=result["total_score"],
    )
    db.add(evaluation)
    await db.flush()
    await db.refresh(evaluation)

    return EvaluateResponse(
        id=str(evaluation.id),
        mode=evaluation.mode,
        results=[AnswerResult(**r) for r in result["results"]],
        total_score=float(evaluation.total_score),
    )


@router.get("/history", response_model=list[EvaluateResponse])
async def get_evaluate_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(EvaluationResult)
        .where(EvaluationResult.user_id == current_user.id)
        .order_by(EvaluationResult.created_at.desc())
    )
    items = result.scalars().all()
    return [
        EvaluateResponse(
            id=str(e.id),
            mode=e.mode,
            results=[AnswerResult(**r) for r in e.results],
            total_score=float(e.total_score),
        )
        for e in items
    ]


@router.get("/history/{eval_id}", response_model=EvaluateResponse)
async def get_evaluation(
    eval_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(EvaluationResult).where(
            EvaluationResult.id == uuid.UUID(eval_id),
            EvaluationResult.user_id == current_user.id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found")
    return EvaluateResponse(
        id=str(item.id),
        mode=item.mode,
        results=[AnswerResult(**r) for r in item.results],
        total_score=float(item.total_score),
    )


@router.delete("/history/{eval_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_evaluation(
    eval_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(EvaluationResult).where(
            EvaluationResult.id == uuid.UUID(eval_id),
            EvaluationResult.user_id == current_user.id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found")
    await db.delete(item)