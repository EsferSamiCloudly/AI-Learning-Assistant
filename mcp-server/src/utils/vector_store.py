import asyncpg
import numpy as np


async def store_chunks(
    conn: asyncpg.Connection,
    document_id: str,
    user_id: str,
    chunks: list[dict],
) -> None:
    """
    Bulk insert chunks with embeddings into vectors.document_chunks.
    Each chunk: {"chunk_index": int, "page_number": int, "content": str, "embedding": list[float]}
    """
    await conn.executemany(
        """
        INSERT INTO vectors.document_chunks
            (document_id, user_id, chunk_index, page_number, content, embedding)
        VALUES ($1, $2, $3, $4, $5, $6)
        """,
        [
            (
                document_id,
                user_id,
                chunk["chunk_index"],
                chunk.get("page_number"),
                chunk["content"],
                np.array(chunk["embedding"], dtype=np.float32),
            )
            for chunk in chunks
        ],
    )


async def similarity_search(
    conn: asyncpg.Connection,
    query_embedding: list[float],
    document_id: str,
    user_id: str,
    top_k: int = 5,
) -> list[dict]:
    """
    Find top-k most similar chunks for a given query embedding.
    Filtered strictly by document_id and user_id.
    """
    rows = await conn.fetch(
        """
        SELECT content, page_number,
               1 - (embedding <=> $1) AS similarity
        FROM vectors.document_chunks
        WHERE document_id = $2 AND user_id = $3
        ORDER BY embedding <=> $1
        LIMIT $4
        """,
        np.array(query_embedding, dtype=np.float32),
        document_id,
        user_id,
        top_k,
    )
    return [
        {
            "content": row["content"],
            "page_number": row["page_number"],
            "similarity": float(row["similarity"]),
        }
        for row in rows
    ]


async def delete_chunks_by_document(
    conn: asyncpg.Connection,
    document_id: str,
) -> None:
    await conn.execute(
        "DELETE FROM vectors.document_chunks WHERE document_id = $1",
        document_id,
    )