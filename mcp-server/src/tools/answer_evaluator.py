from src.main import mcp
from src.graphs.evaluator_graph import evaluator_graph, EvaluatorState


@mcp.tool(name="answer_evaluator")
async def answer_evaluator(
    pairs: list[dict],
    reference_content: str | None = None,
    mode: str = "single",
) -> dict:
    """Evaluate student answers against reference content."""
    state: EvaluatorState = {
        "pairs": pairs,
        "reference_content": reference_content,
        "mode": mode,
        "results": [],
        "total_score": 0.0,
    }
    result = await evaluator_graph.ainvoke(state)
    return {
        "results": result["results"],
        "total_score": result["total_score"],
    }