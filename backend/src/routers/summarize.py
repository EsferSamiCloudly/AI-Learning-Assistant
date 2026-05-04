import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from ..database import get_db
from ..dependencies import get_current_user
from ..models.db.user import User
from ..models.db.document import Document
from ..models.db.outputs import SummarizationOutput
from ..models.schemas.summarize import SummarizeTextRequest, SummarizePDFRequest, SummarizeResponse
from ..services import mcp_client

router = APIRouter()


@router.post("/text", response_model=SummarizeResponse)
async def summarize_text(
    body: SummarizeTextRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    content = await mcp_client.call_summarizer(
        content=body.content,
        mode=body.mode,
        source_type="text",
    )

    output = SummarizationOutput(
        user_id=current_user.id,
        source_type="text",
        mode=body.mode,
        content=content,
    )
    db.add(output)
    await db.flush()
    await db.refresh(output)

    return SummarizeResponse(id=str(output.id), content=output.content, mode=output.mode)


@router.post("/document", response_model=SummarizeResponse)
async def summarize_document(
    body: SummarizePDFRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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
    joined_content = "\n".join([row[0] for row in chunks])

    content = await mcp_client.call_summarizer(
        content=joined_content,
        mode=body.mode,
        source_type="pdf",
    )

    output = SummarizationOutput(
        user_id=current_user.id,
        document_id=doc.id,
        source_type="pdf",
        mode=body.mode,
        content=content,
    )
    db.add(output)
    await db.flush()
    await db.refresh(output)

    return SummarizeResponse(id=str(output.id), content=output.content, mode=output.mode)


@router.get("/history", response_model=list[SummarizeResponse])
async def get_summarize_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(SummarizationOutput)
        .where(SummarizationOutput.user_id == current_user.id)
        .order_by(SummarizationOutput.created_at.desc())
    )
    items = result.scalars().all()
    return [
        SummarizeResponse(id=str(i.id), content=i.content, mode=i.mode)
        for i in items
    ]


@router.get("/history/{summary_id}", response_model=SummarizeResponse)
async def get_summary(
    summary_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(SummarizationOutput).where(
            SummarizationOutput.id == uuid.UUID(summary_id),
            SummarizationOutput.user_id == current_user.id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Summary not found")
    return SummarizeResponse(id=str(item.id), content=item.content, mode=item.mode)


@router.delete("/history/{summary_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_summary(
    summary_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(SummarizationOutput).where(
            SummarizationOutput.id == uuid.UUID(summary_id),
            SummarizationOutput.user_id == current_user.id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Summary not found")
    await db.delete(item)