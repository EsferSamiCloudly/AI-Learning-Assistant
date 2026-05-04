import json
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage

from src.groq_client import get_llm
from src.guardrails import check_input_safety
from src.prompt_templates import (
    ESSAY_VALIDATION_SYSTEM,
    ESSAY_OUTLINE_SYSTEM,
    ESSAY_WRITER_SYSTEM,
)


class EssayState(TypedDict):
    topic: str
    tone: str
    length: str
    include_outline: bool
    is_valid: bool
    rejection_reason: str
    outline: str | None
    essay: str


async def validate_topic(state: EssayState) -> EssayState:
    # Guardrail check first
    is_safe, reason = await check_input_safety(state["topic"])
    if not is_safe:
        return {**state, "is_valid": False, "rejection_reason": reason}

    llm = get_llm()
    response = await llm.ainvoke([
        HumanMessage(content=f"{ESSAY_VALIDATION_SYSTEM}\n\nTopic: {state['topic']}")
    ])
    try:
        result = json.loads(response.content.strip())
        return {
            **state,
            "is_valid": result.get("valid", False),
            "rejection_reason": result.get("reason", ""),
        }
    except Exception:
        return {**state, "is_valid": True, "rejection_reason": ""}


async def generate_outline(state: EssayState) -> EssayState:
    llm = get_llm()
    prompt = ESSAY_OUTLINE_SYSTEM.format(topic=state["topic"])
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    try:
        outline_data = json.loads(response.content.strip())
        sections = outline_data.get("sections", [])
        outline_text = "\n".join([f"- {s}" for s in sections])
        return {**state, "outline": outline_text}
    except Exception:
        return {**state, "outline": None}


async def write_essay(state: EssayState) -> EssayState:
    llm = get_llm()
    outline_instruction = (
        f"Follow this outline:\n{state['outline']}"
        if state.get("outline")
        else "Structure the essay naturally."
    )
    prompt = ESSAY_WRITER_SYSTEM.format(
        topic=state["topic"],
        tone=state["tone"],
        length=state["length"],
        outline_instruction=outline_instruction,
    )
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    return {**state, "essay": response.content}


def route_after_validation(state: EssayState) -> str:
    if not state["is_valid"]:
        return "rejected"
    if state["include_outline"]:
        return "generate_outline"
    return "write_essay"


async def reject_topic(state: EssayState) -> EssayState:
    return {**state, "essay": f"⚠️ I cannot write this essay: {state['rejection_reason']}. Please choose an appropriate educational topic."}


def build_essay_graph():
    graph = StateGraph(EssayState)
    graph.add_node("validate_topic", validate_topic)
    graph.add_node("generate_outline", generate_outline)
    graph.add_node("write_essay", write_essay)
    graph.add_node("rejected", reject_topic)
    graph.set_entry_point("validate_topic")
    graph.add_conditional_edges(
        "validate_topic",
        route_after_validation,
        {
            "rejected": "rejected",
            "generate_outline": "generate_outline",
            "write_essay": "write_essay",
        },
    )
    graph.add_edge("rejected", END) 
    graph.add_edge("generate_outline", "write_essay")
    graph.add_edge("write_essay", END)
    return graph.compile()


essay_graph = build_essay_graph()