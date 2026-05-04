import httpx
from ..config import settings


async def call_chatbot(
    question: str,
    session_id: str,
    user_id: str,
    mode: str,
    document_id: str | None,
    message_history: list[dict],
) -> str:
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{settings.MCP_SERVER_URL}/tools/educational_chatbot",
            json={
                "question": question,
                "session_id": session_id,
                "user_id": user_id,
                "mode": mode,
                "document_id": document_id,
                "message_history": message_history,
            },
        )
        response.raise_for_status()
        return response.json()["answer"]


async def call_essay_writer(
    topic: str,
    tone: str,
    length: str,
    include_outline: bool,
) -> str:
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{settings.MCP_SERVER_URL}/tools/ai_essay_writer",
            json={
                "topic": topic,
                "tone": tone,
                "length": length,
                "include_outline": include_outline,
            },
        )
        response.raise_for_status()
        return response.json()["essay"]


async def call_summarizer(
    content: str,
    mode: str,
    source_type: str,
) -> str:
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{settings.MCP_SERVER_URL}/tools/text_pdf_summarizer",
            json={
                "content": content,
                "mode": mode,
                "source_type": source_type,
            },
        )
        response.raise_for_status()
        return response.json()["summary"]


async def call_question_generator(
    content: str,
    difficulty: str,
    count: int,
    domain: str | None,
) -> list[dict]:
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{settings.MCP_SERVER_URL}/tools/question_generator",
            json={
                "content": content,
                "difficulty": difficulty,
                "count": count,
                "domain": domain,
            },
        )
        response.raise_for_status()
        return response.json()["questions"]


async def call_answer_evaluator(
    pairs: list[dict],
    reference_content: str | None,
    mode: str,
) -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{settings.MCP_SERVER_URL}/tools/answer_evaluator",
            json={
                "pairs": pairs,
                "reference_content": reference_content,
                "mode": mode,
            },
        )
        response.raise_for_status()
        return response.json()