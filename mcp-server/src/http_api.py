import base64
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.db import get_pool, close_pool
from src.embeddings import get_model, get_embeddings_batch
from src.graphs.chatbot_graph import chatbot_graph, ChatbotState
from src.graphs.essay_graph import essay_graph, EssayState
from src.graphs.summarizer_graph import summarizer_graph, SummarizerState
from src.graphs.question_graph import question_graph, QuestionState
from src.graphs.evaluator_graph import evaluator_graph, EvaluatorState
from src.utils.pdf_parser import parse_pdf_bytes
from src.utils.text_splitter import split_pages
from src.utils.vector_store import store_chunks


@asynccontextmanager
async def lifespan(app):
    await get_pool()
    get_model()
    yield
    await close_pool()


app = FastAPI(lifespan=lifespan)


# ─── Request Models ──────────────────────────────────────────────────────────

class ChatbotRequest(BaseModel):
    question: str
    session_id: str
    user_id: str
    mode: str
    document_id: str | None = None
    message_history: list[dict] = []


class EssayRequest(BaseModel):
    topic: str
    tone: str = "academic"
    length: str = "medium"
    include_outline: bool = False


class SummarizerRequest(BaseModel):
    content: str
    mode: str = "short"
    source_type: str = "text"


class QuestionRequest(BaseModel):
    content: str
    difficulty: str = "medium"
    count: int = 5
    domain: str | None = None


class EvaluatorRequest(BaseModel):
    pairs: list[dict]
    reference_content: str | None = None
    mode: str = "single"


class EmbedRequest(BaseModel):
    document_id: str
    file_bytes_b64: str
    filename: str
    user_id: str


# ─── AI Tool Endpoints ────────────────────────────────────────────────────────

@app.post("/tools/educational_chatbot")
async def educational_chatbot(body: ChatbotRequest):
    state: ChatbotState = {
        "question": body.question,
        "session_id": body.session_id,
        "user_id": body.user_id,
        "mode": body.mode,
        "document_id": body.document_id,
        "message_history": body.message_history,
        "retrieved_chunks": [],
        "answer": "",
    }
    result = await chatbot_graph.ainvoke(state)
    return {"answer": result["answer"]}


@app.post("/tools/ai_essay_writer")
async def ai_essay_writer(body: EssayRequest):
    state: EssayState = {
        "topic": body.topic,
        "tone": body.tone,
        "length": body.length,
        "include_outline": body.include_outline,
        "is_valid": False,
        "rejection_reason": "",
        "outline": None,
        "essay": "",
    }
    result = await essay_graph.ainvoke(state)
    # Return essay even if it contains a blocked message
    return {"essay": result["essay"]}


@app.post("/tools/text_pdf_summarizer")
async def text_pdf_summarizer(body: SummarizerRequest):
    state: SummarizerState = {
        "content": body.content,
        "mode": body.mode,
        "chunks": [],
        "chunk_summaries": [],
        "final_summary": "",
    }
    result = await summarizer_graph.ainvoke(state)
    return {"summary": result["final_summary"]}


@app.post("/tools/question_generator")
async def question_generator(body: QuestionRequest):
    state: QuestionState = {
        "content": body.content,
        "difficulty": body.difficulty,
        "count": body.count,
        "domain": body.domain,
        "questions": [],
        "retry_count": 0,
    }
    result = await question_graph.ainvoke(state)
    return {"questions": result["questions"]}


@app.post("/tools/answer_evaluator")
async def answer_evaluator(body: EvaluatorRequest):
    state: EvaluatorState = {
        "pairs": body.pairs,
        "reference_content": body.reference_content,
        "mode": body.mode,
        "results": [],
        "total_score": 0.0,
    }
    result = await evaluator_graph.ainvoke(state)
    return {"results": result["results"], "total_score": result["total_score"]}


# ─── PDF Embedding Endpoint ───────────────────────────────────────────────────

@app.post("/embed")
async def embed_document(body: EmbedRequest):
    file_bytes = base64.b64decode(body.file_bytes_b64)

    pages = parse_pdf_bytes(file_bytes)
    chunks = split_pages(pages)

    if not chunks:
        raise HTTPException(status_code=400, detail="No content could be extracted from the PDF")

    texts = [c["content"] for c in chunks]
    embeddings = get_embeddings_batch(texts)
    for i, chunk in enumerate(chunks):
        chunk["embedding"] = embeddings[i]

    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("SET search_path TO app, auth, vectors, public")

        doc = await conn.fetchrow(
            "SELECT id FROM app.documents WHERE id = $1::uuid",
            body.document_id,
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail=f"Document {body.document_id} not found in database",
            )

        await conn.execute(
            "UPDATE app.documents SET embed_status='processing' WHERE id=$1::uuid",
            body.document_id,
        )
        await store_chunks(conn, body.document_id, body.user_id, chunks)
        await conn.execute(
            "UPDATE app.documents SET embed_status='done', page_count=$1 WHERE id=$2::uuid",
            len(pages),
            body.document_id,
        )

    return {"status": "done", "chunks": len(chunks), "pages": len(pages)}