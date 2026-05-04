import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
import redis.asyncio as aioredis

from ..config import settings
from ..models.db.user import User, RefreshToken

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: str, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": user_id,
        "email": email,
        "jti": str(uuid.uuid4()),
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token() -> tuple[str, str]:
    raw_token = secrets.token_urlsafe(64)
    hashed_token = hashlib.sha256(raw_token.encode()).hexdigest()
    return raw_token, hashed_token


async def blacklist_access_token(
    jti: str, expire_seconds: int, redis: aioredis.Redis
) -> None:
    await redis.set(f"blacklist:jti:{jti}", "1", ex=expire_seconds)


async def register_user(
    db: AsyncSession,
    email: str,
    password: str,
    full_name: str | None,
) -> User:
    # Check email not taken
    result = await db.execute(select(User).where(User.email == email))
    existing = result.scalar_one_or_none()
    if existing:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(
        email=email,
        password_hash=hash_password(password),
        full_name=full_name,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def login_user(
    db: AsyncSession,
    redis: aioredis.Redis,
    email: str,
    password: str,
) -> tuple[str, str]:
    from fastapi import HTTPException, status

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(str(user.id), user.email)
    raw_refresh, hashed_refresh = create_refresh_token()

    expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )

    refresh_token_obj = RefreshToken(
        user_id=user.id,
        token_hash=hashed_refresh,
        expires_at=expires_at,
    )
    db.add(refresh_token_obj)
    await db.flush()

    # Store in Redis with TTL
    ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
    await redis.set(f"refresh:{hashed_refresh}", str(user.id), ex=ttl)

    return access_token, raw_refresh


async def refresh_tokens(
    db: AsyncSession,
    redis: aioredis.Redis,
    raw_refresh_token: str,
) -> tuple[str, str]:
    from fastapi import HTTPException, status

    hashed = hashlib.sha256(raw_refresh_token.encode()).hexdigest()

    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == hashed)
    )
    token_obj = result.scalar_one_or_none()

    if not token_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    if token_obj.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        )

    # Load user
    user_result = await db.execute(
        select(User).where(User.id == token_obj.user_id)
    )
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Delete old token
    await db.execute(
        delete(RefreshToken).where(RefreshToken.token_hash == hashed)
    )
    await redis.delete(f"refresh:{hashed}")

    # Create new tokens
    new_access = create_access_token(str(user.id), user.email)
    new_raw_refresh, new_hashed_refresh = create_refresh_token()

    expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    new_token_obj = RefreshToken(
        user_id=user.id,
        token_hash=new_hashed_refresh,
        expires_at=expires_at,
    )
    db.add(new_token_obj)
    await db.flush()

    ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
    await redis.set(f"refresh:{new_hashed_refresh}", str(user.id), ex=ttl)

    return new_access, new_raw_refresh


async def logout_user(
    db: AsyncSession,
    redis: aioredis.Redis,
    jti: str,
    token_exp: int,
    user_id: str,
    raw_refresh_token: str | None,
) -> None:
    # Blacklist access token
    now = int(datetime.now(timezone.utc).timestamp())
    remaining = max(token_exp - now, 0)
    await blacklist_access_token(jti, remaining, redis)

    # Delete refresh token if provided
    if raw_refresh_token:
        hashed = hashlib.sha256(raw_refresh_token.encode()).hexdigest()
        await db.execute(
            delete(RefreshToken).where(RefreshToken.token_hash == hashed)
        )
        await redis.delete(f"refresh:{hashed}")