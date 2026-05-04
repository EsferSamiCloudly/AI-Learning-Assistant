import asyncpg
from pgvector.asyncpg import register_vector
from urllib.parse import urlparse, urlunparse, quote
from src.config import settings

_pool: asyncpg.Pool | None = None


def _get_asyncpg_dsn() -> str:
    url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    parsed = urlparse(url)
    encoded_password = quote(str(parsed.password), safe="")
    netloc = f"{parsed.username}:{encoded_password}@{parsed.hostname}:{parsed.port}"
    return urlunparse(parsed._replace(netloc=netloc))


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            dsn=_get_asyncpg_dsn(),
            min_size=2,
            max_size=10,
            init=_init_connection,
        )
    return _pool


async def _init_connection(conn: asyncpg.Connection) -> None:
    await register_vector(conn)
    await conn.execute("SET search_path TO app, auth, vectors, public")


async def close_pool() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None