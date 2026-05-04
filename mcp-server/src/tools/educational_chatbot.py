from src.main import mcp
from src.graphs.chatbot_graph import chatbot_graph, ChatbotState


@mcp.tool(name="educational_chatbot")
async def educational_chatbot(
    question: str,
    session_id: str,
    user_id: str,
    mode: str,
    document_id: str | None = None,
    message_history: list[dict] | None = None,
) -> dict:
    """Educational chatbot with PDF RAG and general knowledge modes."""
    state: ChatbotState = {
        "question": question,
        "session_id": session_id,
        "user_id": user_id,
        "mode": mode,
        "document_id": document_id,
        "message_history": message_history or [],
        "retrieved_chunks": [],
        "answer": "",
    }
    result = await chatbot_graph.ainvoke(state)
    return {"answer": result["answer"]}