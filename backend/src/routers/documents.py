import base64
import httpx
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..dependencies import get_current_user
from ..models.db.user import User
from ..models.db.document import Document
from ..models.schemas.document import DocumentUploadResponse, DocumentResponse
from ..config import settings

router = APIRouter()


async def trigger_embedding(document_id: str, file_bytes_b64: str, filename: str, user_id: str):
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            await client.post(
                f"{settings.MCP_SERVER_URL}/embed",
                json={
                    "document_id": document_id,
                    "file_bytes_b64": file_bytes_b64,
                    "filename": filename,
                    "user_id": user_id,
                }
            )
        except Exception as e:
            print(f"Embedding failed: {e}")


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported",
        )

    file_bytes = await file.read()
    file_bytes_b64 = base64.b64encode(file_bytes).decode()

    document = Document(
        user_id=current_user.id,
        filename=file.filename,
        embed_status="processing",
    )
    db.add(document)
    await db.flush()
    await db.refresh(document)

    # Commit BEFORE triggering background task
    # so MCP server can find the document in DB
    await db.commit()

    background_tasks.add_task(
        trigger_embedding,
        str(document.id),
        file_bytes_b64,
        file.filename,
        str(current_user.id),
    )

    return DocumentUploadResponse(
        id=str(document.id),
        filename=document.filename,
        embed_status=document.embed_status,
        celery_task_id=str(document.id),
        created_at=document.created_at,
    )


@router.get("/", response_model=list[DocumentResponse])
async def get_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Document)
        .where(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
    )
    documents = result.scalars().all()
    return [
        DocumentResponse(
            id=str(d.id),
            filename=d.filename,
            embed_status=d.embed_status,
            page_count=d.page_count,
            created_at=d.created_at,
        )
        for d in documents
    ]