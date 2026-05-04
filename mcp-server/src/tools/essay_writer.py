from src.main import mcp
from src.graphs.essay_graph import essay_graph, EssayState


@mcp.tool(name="ai_essay_writer")
async def ai_essay_writer(
    topic: str,
    tone: str = "academic",
    length: str = "medium",
    include_outline: bool = False,
) -> dict:
    """Generate a structured essay on any topic."""
    state: EssayState = {
        "topic": topic,
        "tone": tone,
        "length": length,
        "include_outline": include_outline,
        "is_valid": False,
        "rejection_reason": "",
        "outline": None,
        "essay": "",
    }
    result = await essay_graph.ainvoke(state)
    return {"essay": result["essay"]}