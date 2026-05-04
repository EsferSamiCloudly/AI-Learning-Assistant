from src.main import mcp
from src.graphs.question_graph import question_graph, QuestionState


@mcp.tool(name="question_generator")
async def question_generator(
    content: str,
    difficulty: str = "medium",
    count: int = 5,
    domain: str | None = None,
) -> dict:
    """Generate questions from provided content."""
    state: QuestionState = {
        "content": content,
        "difficulty": difficulty,
        "count": count,
        "domain": domain,
        "questions": [],
        "retry_count": 0,
    }
    result = await question_graph.ainvoke(state)
    return {"questions": result["questions"]}