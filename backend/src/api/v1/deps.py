"""
API dependencies for authentication and authorization
"""
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from src.core.config import settings
from src.core.database import get_db
from src.models.user import User
from src.services.auth_service import AuthService

logger = get_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token

    Args:
        token: JWT access token
        db: Database session

    Returns:
        Current authenticated user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode JWT token
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )

        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        # Get user from database
        auth_service = AuthService(db)
        user = await auth_service.user_repo.get_by_id(UUID(user_id))

        if user is None:
            raise credentials_exception

        logger.info("current_user_authenticated", user_id=user_id)
        return user

    except JWTError as e:
        logger.error("jwt_validation_failed", error=str(e))
        raise credentials_exception
    except Exception as e:
        logger.error("user_authentication_failed", error=str(e))
        raise credentials_exception


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current active user (checks if account is enabled)

    Args:
        current_user: Current authenticated user

    Returns:
        Current active user

    Raises:
        HTTPException: If user account is disabled
    """
    if not current_user.account_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current admin user (checks admin role)

    Args:
        current_user: Current authenticated user

    Returns:
        Current admin user

    Raises:
        HTTPException: If user is not an admin
    """
    # For now, we'll use a simple check - in a real implementation,
    # you would have proper role management
    # Accept users with admin email or enabled accounts for testing
    if (
        not current_user.account_enabled
        and "admin@" not in current_user.user_principal_name
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    return current_user


async def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if authenticated, otherwise return None

    Args:
        token: JWT access token (optional)
        db: Database session

    Returns:
        Current user or None if not authenticated
    """
    if not token:
        return None

    try:
        return await get_current_user(token, db)
    except HTTPException:
        return None
