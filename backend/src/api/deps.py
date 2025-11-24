"""
API dependencies for dependency injection
"""
from typing import Annotated
from uuid import UUID

import redis.asyncio as aioredis
import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.database import get_db
from ..core.security import decode_token, verify_token_type
from ..models.user import User
from ..repositories.user_repository import UserRepository
from ..schemas.token import TokenPayload

logger = structlog.get_logger(__name__)

# OAuth2 scheme for JWT token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")

# Redis client (singleton pattern)
_redis_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """
    Get Redis client for caching and rate limiting.

    Returns:
        Redis client instance
    """
    global _redis_client

    if _redis_client is None:
        _redis_client = await aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )

    return _redis_client


async def close_redis() -> None:
    """Close Redis connection on application shutdown"""
    global _redis_client

    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("redis_connection_closed")


async def get_current_token_payload(
    token: Annotated[str, Depends(oauth2_scheme)]
) -> TokenPayload:
    """
    Extract and validate JWT token payload.

    Args:
        token: JWT token from Authorization header

    Returns:
        Validated token payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode token
        logger.info("debug_token_received", token=token)
        payload = decode_token(token)

        # Verify it's an access token
        if not verify_token_type(payload, "access"):
            logger.warning(
                "invalid_token_type", expected="access", got=payload.get("type")
            )
            raise credentials_exception

        # Extract user_id from sub claim
        user_id: str | None = payload.get("sub")
        if user_id is None:
            logger.warning("missing_subject_in_token")
            raise credentials_exception

        # Construct TokenPayload
        token_payload = TokenPayload(
            sub=user_id,
            exp=payload.get("exp"),
            iat=payload.get("iat"),
            type=payload.get("type"),
            tenants=payload.get("tenants", []),
            email=payload.get("email"),
        )

        return token_payload

    except JWTError as e:
        logger.warning("jwt_validation_failed", error=str(e))
        raise credentials_exception
    except Exception as e:
        logger.error("token_validation_error", error=str(e))
        raise credentials_exception


async def get_current_user(
    token_payload: Annotated[TokenPayload, Depends(get_current_token_payload)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Get current authenticated user from token.

    Args:
        token_payload: Validated token payload
        db: Database session

    Returns:
        User model instance

    Raises:
        HTTPException: If user not found or account disabled
    """
    try:
        user_id = UUID(token_payload.sub)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
        )

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if user is None:
        logger.warning("user_not_found_from_token", user_id=str(user_id))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not user.account_enabled:
        logger.warning("disabled_user_attempted_access", user_id=str(user_id))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    return user


async def get_current_tenant_id(
    token_payload: Annotated[TokenPayload, Depends(get_current_token_payload)],
) -> UUID:
    """
    Get current tenant ID from token.

    For multi-tenant scenarios, this can be extended to allow selecting
    a specific tenant from the tenants list in the token.

    For now, we return the first tenant in the list.

    Args:
        token_payload: Validated token payload

    Returns:
        Tenant UUID

    Raises:
        HTTPException: If no tenants in token
    """
    if not token_payload.tenants:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tenants associated with this user",
        )

    try:
        tenant_id = UUID(token_payload.tenants[0])
    except (ValueError, IndexError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tenant ID in token",
        )

    return tenant_id
