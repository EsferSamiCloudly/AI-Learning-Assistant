from src.main import mcp
from src.graphs.summarizer_graph import summarizer_graph, SummarizerState


@mcp.tool(name="text_pdf_summarizer")
async def text_pdf_summarizer(
    content: str,
    mode: str = "short",
    source_type: str = "text",
) -> dict:
    """Summarize text or PDF content."""
    state: SummarizerState = {
        "content": content,
        "mode": mode,
        "chunks": [],
        "chunk_summaries": [],
        "final_summary": "",
    }
    result = await summarizer_graph.ainvoke(state)
    return {"summary": result["final_summary"]}