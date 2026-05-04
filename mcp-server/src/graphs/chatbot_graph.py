import json
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage

from src.groq_client import get_llm
from src.embeddings import get_embedding
from src.prompt_templates import chatbot_pdf_prompt, chatbot_general_prompt
from src.db import get_pool
from src.utils.vector_store import similarity_search
from src.guardrails import check_input_safety

class ChatbotState(TypedDict):
    question: str
    mode: str
    document_id: str | None
    user_id: str
    session_id: str
    message_history: list[dict]
    retrieved_chunks: list[dict]
    answer: str


async def retrieve_context(state: ChatbotState) -> ChatbotState:
    # Guardrail check
    is_safe, reason = await check_input_safety(state["question"])
    if not is_safe:
        return {**state, "retrieved_chunks": [], "answer": f"I cannot process this request: {reason}"}

    if state["mode"] == "general" or not state["document_id"]:
        return {**state, "retrieved_chunks": []}

    query_embedding = get_embedding(state["question"])
    pool = await get_pool()
    async with pool.acquire() as conn:
        chunks = await similarity_search(
            conn=conn,
            query_embedding=query_embedding,
            document_id=state["document_id"],
            user_id=state["user_id"],
            top_k=8,
        )
    return {**state, "retrieved_chunks": chunks}


async def generate_answer(state: ChatbotState) -> ChatbotState:
    # If guardrail already set answer, skip LLM call
    if state.get("answer"):
        return state

    llm = get_llm()

    # Build history messages
    history = []
    for msg in state["message_history"][:-1]:
        if msg["role"] == "user":
            history.append(HumanMessage(content=msg["content"]))
        else:
            history.append(AIMessage(content=msg["content"]))

    if state["mode"] == "pdf" and state["retrieved_chunks"]:
        context = "\n\n".join([
            f"[Page {c['page_number']}]: {c['content']}"
            for c in state["retrieved_chunks"]
        ])
        chain = chatbot_pdf_prompt | llm
        response = await chain.ainvoke({
            "context": context,
            "history": history,
            "question": state["question"],
        })
    elif state["mode"] == "pdf" and not state["retrieved_chunks"]:
        chain = chatbot_general_prompt | llm
        response = await chain.ainvoke({
            "history": history,
            "question": f"Note: No relevant context was found in the document for this question. Answer from general knowledge if possible.\n\n{state['question']}",
        })
    else:
        chain = chatbot_general_prompt | llm
        response = await chain.ainvoke({
            "history": history,
            "question": state["question"],
        })

    return {**state, "answer": response.content}


def build_chatbot_graph():
    graph = StateGraph(ChatbotState)
    graph.add_node("retrieve_context", retrieve_context)
    graph.add_node("generate_answer", generate_answer)
    graph.set_entry_point("retrieve_context")
    graph.add_edge("retrieve_context", "generate_answer")
    graph.add_edge("generate_answer", END)
    return graph.compile()


chatbot_graph = build_chatbot_graph()