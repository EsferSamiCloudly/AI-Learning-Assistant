import json
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage

from src.groq_client import get_llm
from src.guardrails import check_input_safety
from src.prompt_templates import QUESTION_GENERATOR_SYSTEM


class QuestionState(TypedDict):
    content: str
    difficulty: str
    count: int
    domain: str | None
    questions: list[dict]
    retry_count: int


async def generate_questions(state: QuestionState) -> QuestionState:
    # Guardrail check only on first attempt
    if state["retry_count"] == 0:
        is_safe, reason = await check_input_safety(state["content"][:1000])
        if not is_safe:
            return {**state, "questions": [{
                "question": f"⚠️ Content blocked: {reason}. Please provide appropriate educational content.",
                "expected_answer": "",
                "difficulty": state["difficulty"],
            }]}

    llm = get_llm()
    prompt = QUESTION_GENERATOR_SYSTEM.format(
        count=state["count"],
        difficulty=state["difficulty"],
        domain=state["domain"] or "general",
        content=state["content"],
    )
    response = await llm.ainvoke([HumanMessage(content=prompt)])

    try:
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        questions = json.loads(raw.strip())
        return {**state, "questions": questions}
    except Exception:
        return {**state, "questions": []}


async def validate_questions(state: QuestionState) -> QuestionState:
    # Skip validation if blocked by guardrail
    if (
        len(state["questions"]) == 1
        and state["questions"][0].get("question", "").startswith("⚠️")
    ):
        return state

    questions = state["questions"]
    valid = [
        q for q in questions
        if isinstance(q, dict)
        and "question" in q
        and "expected_answer" in q
        and "difficulty" in q
    ]

    if len(valid) < state["count"] and state["retry_count"] < 1:
        return {**state, "questions": [], "retry_count": state["retry_count"] + 1}

    return {**state, "questions": valid[:state["count"]]}


def route_after_validation(state: QuestionState) -> str:
    if not state["questions"] and state["retry_count"] <= 1:
        return "generate_questions"
    return END


def build_question_graph():
    graph = StateGraph(QuestionState)
    graph.add_node("generate_questions", generate_questions)
    graph.add_node("validate_questions", validate_questions)
    graph.set_entry_point("generate_questions")
    graph.add_edge("generate_questions", "validate_questions")
    graph.add_conditional_edges(
        "validate_questions",
        route_after_validation,
        {
            "generate_questions": "generate_questions",
            END: END,
        },
    )
    return graph.compile()


question_graph = build_question_graph()