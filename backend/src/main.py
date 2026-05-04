from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .config import settings
from .redis_client import redis_client, close_redis
from .routers import auth, users, chat, essay, summarize, questions, evaluate, documents, tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown
    await close_redis()


limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="AI Learning Assistant API",
    version="2.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(essay.router, prefix="/essay", tags=["essay"])
app.include_router(summarize.router, prefix="/summarize", tags=["summarize"])
app.include_router(questions.router, prefix="/questions", tags=["questions"])
app.include_router(evaluate.router, prefix="/evaluate", tags=["evaluate"])
app.include_router(documents.router, prefix="/documents", tags=["documents"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "2.0.0"}