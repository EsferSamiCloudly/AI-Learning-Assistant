from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage

from src.groq_client import get_llm
from src.guardrails import check_input_safety
from src.prompt_templates import SUMMARIZER_CHUNK_SYSTEM, SUMMARIZER_MERGE_SYSTEM
from src.utils.text_splitter import split_text


class SummarizerState(TypedDict):
    content: str
    mode: str
    chunks: list[str]
    chunk_summaries: list[str]
    final_summary: str


async def split_content(state: SummarizerState) -> SummarizerState:
    # Guardrail check on first 1000 chars as sample
    is_safe, reason = await check_input_safety(state["content"][:1000])
    if not is_safe:
        return {
            **state,
            "chunks": [],
            "chunk_summaries": [],
            "final_summary": f"⚠️ Content blocked: {reason}. Please provide appropriate educational content for summarization.",
        }

    chunks = split_text(state["content"], chunk_size=1500, chunk_overlap=100)
    return {**state, "chunks": chunks}


async def summarize_chunks(state: SummarizerState) -> SummarizerState:
    # Skip if blocked by guardrail
    if not state["chunks"]:
        return {**state, "chunk_summaries": [state.get("final_summary", "")]}

    llm = get_llm()
    summaries = []

    for chunk in state["chunks"]:
        prompt = SUMMARIZER_CHUNK_SYSTEM.format(mode=state["mode"], chunk=chunk)
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        summaries.append(response.content.strip())

    return {**state, "chunk_summaries": summaries}


async def merge_summaries(state: SummarizerState) -> SummarizerState:
    # Skip if blocked by guardrail — final_summary already set
    if not state["chunks"] and state.get("final_summary"):
        return state

    if len(state["chunk_summaries"]) == 1:
        return {**state, "final_summary": state["chunk_summaries"][0]}

    llm = get_llm()
    joined = "\n\n---\n\n".join(state["chunk_summaries"])
    prompt = SUMMARIZER_MERGE_SYSTEM.format(mode=state["mode"], summaries=joined)
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    return {**state, "final_summary": response.content.strip()}


def build_summarizer_graph():
    graph = StateGraph(SummarizerState)
    graph.add_node("split_content", split_content)
    graph.add_node("summarize_chunks", summarize_chunks)
    graph.add_node("merge_summaries", merge_summaries)
    graph.set_entry_point("split_content")
    graph.add_edge("split_content", "summarize_chunks")
    graph.add_edge("summarize_chunks", "merge_summaries")
    graph.add_edge("merge_summaries", END)
    return graph.compile()


summarizer_graph = build_summarizer_graph()