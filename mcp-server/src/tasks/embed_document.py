import asyncio
import base64
import asyncpg
from pgvector.asyncpg import register_vector

from src.celery_app import celery_app
from src.config import settings
from src.utils.pdf_parser import parse_pdf_bytes
from src.utils.text_splitter import split_pages
from src.embeddings import get_embeddings_batch
from src.utils.vector_store import store_chunks


async def _embed_document(
    document_id: str,
    file_bytes: bytes,
    filename: str,
    user_id: str,
) -> int:
    # Parse PDF in memory
    pages = parse_pdf_bytes(file_bytes)
    chunks = split_pages(pages)
    page_count = len(pages)

    if not chunks:
        raise ValueError("No content could be extracted from the PDF")

    # Get embeddings for all chunks
    texts = [chunk["content"] for chunk in chunks]
    embeddings = get_embeddings_batch(texts)

    # Attach embeddings to chunks
    for i, chunk in enumerate(chunks):
        chunk["embedding"] = embeddings[i]

    # Connect to PostgreSQL directly (not using the shared pool — Celery runs in separate process)
    dsn = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(dsn=dsn)

    try:
        await register_vector(conn)
        await conn.execute("SET search_path TO app, auth, vectors, public")

        # Update status to processing
        await conn.execute(
            "UPDATE app.documents SET embed_status = 'processing' WHERE id = $1",
            document_id,
        )

        # Store all chunks
        await store_chunks(conn, document_id, user_id, chunks)

        # Update status to done
        await conn.execute(
            "UPDATE app.documents SET embed_status = 'done', page_count = $1 WHERE id = $2",
            page_count,
            document_id,
        )

    except Exception as e:
        await conn.execute(
            "UPDATE app.documents SET embed_status = 'failed' WHERE id = $1",
            document_id,
        )
        raise e

    finally:
        await conn.close()

    return page_count


@celery_app.task(bind=True, name="embed_document")
def embed_document(
    self,
    document_id: str,
    file_bytes_b64: str,
    filename: str,
    user_id: str,
) -> dict:
    """
    Celery task: decode PDF bytes, parse, chunk, embed, store in pgvector.
    Runs in a separate worker process.
    """
    try:
        file_bytes = base64.b64decode(file_bytes_b64)
        page_count = asyncio.run(
            _embed_document(document_id, file_bytes, filename, user_id)
        )
        return {"status": "done", "page_count": page_count, "document_id": document_id}

    except Exception as exc:
        raise self.retry(exc=exc, countdown=5, max_retries=2)