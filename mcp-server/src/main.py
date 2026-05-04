from contextlib import asynccontextmanager
from fastmcp import FastMCP
from src.db import get_pool, close_pool
from src.redis_client import close_redis


@asynccontextmanager
async def lifespan(app):
    await get_pool()
    from src.embeddings import get_model
    get_model()
    yield
    await close_pool()
    await close_redis()


mcp = FastMCP(
    name="ai-learning-assistant",
    lifespan=lifespan,
)

from src.tools import educational_chatbot  # noqa: F401, E402
from src.tools import essay_writer         # noqa: F401, E402
from src.tools import summarizer           # noqa: F401, E402
from src.tools import question_generator   # noqa: F401, E402
from src.tools import answer_evaluator     # noqa: F401, E402