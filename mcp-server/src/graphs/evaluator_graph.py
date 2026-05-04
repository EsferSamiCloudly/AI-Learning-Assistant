import json
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage

from src.groq_client import get_llm
from src.guardrails import check_input_safety
from src.prompt_templates import EVALUATOR_SYSTEM


class EvaluatorState(TypedDict):
    pairs: list[dict]
    reference_content: str | None
    mode: str
    results: list[dict]
    total_score: float


async def grade_answers(state: EvaluatorState) -> EvaluatorState:
    # Guardrail check on first pair as representative sample
    if state["pairs"]:
        sample = (
            state["pairs"][0].get("question", "") +
            " " +
            state["pairs"][0].get("student_answer", "")
        )
        is_safe, reason = await check_input_safety(sample)
        if not is_safe:
            return {**state, "results": [{
                "question": "Safety Check",
                "student_answer": "",
                "score": 0.0,
                "feedback": f"⚠️ Content blocked: {reason}. Please ensure your questions and answers are appropriate for an educational context.",
            }], "total_score": 0.0}

    llm = get_llm()
    results = []

    for pair in state["pairs"]:
        reference = (
            pair.get("reference_answer")
            or state.get("reference_content")
            or "Use your knowledge to evaluate."
        )
        prompt = EVALUATOR_SYSTEM.format(
            question=pair["question"],
            reference_answer=reference,
            student_answer=pair["student_answer"],
        )
        response = await llm.ainvoke([HumanMessage(content=prompt)])

        try:
            raw = response.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            graded = json.loads(raw.strip())
            results.append({
                "question": pair["question"],
                "student_answer": pair["student_answer"],
                "score": float(graded.get("score", 0.0)),
                "feedback": graded.get("feedback", ""),
            })
        except Exception:
            results.append({
                "question": pair["question"],
                "student_answer": pair["student_answer"],
                "score": 0.0,
                "feedback": "Could not evaluate this answer.",
            })

    return {**state, "results": results}


async def calculate_total(state: EvaluatorState) -> EvaluatorState:
    if not state["results"]:
        return {**state, "total_score": 0.0}
    # If blocked by guardrail, total_score already set to 0.0
    if state.get("total_score") == 0.0 and len(state["results"]) == 1 and state["results"][0]["question"] == "Safety Check":
        return state
    total = sum(r["score"] for r in state["results"]) / len(state["results"])
    return {**state, "total_score": round(total, 2)}


def build_evaluator_graph():
    graph = StateGraph(EvaluatorState)
    graph.add_node("grade_answers", grade_answers)
    graph.add_node("calculate_total", calculate_total)
    graph.set_entry_point("grade_answers")
    graph.add_edge("grade_answers", "calculate_total")
    graph.add_edge("calculate_total", END)
    return graph.compile()


evaluator_graph = build_evaluator_graph()