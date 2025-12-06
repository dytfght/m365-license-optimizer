"""
Authentication service for user login and token management
"""
from typing import Any
from uuid import UUID

import structlog
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
    verify_token_type,
)
from ..repositories.user_repository import UserRepository
from ..schemas.token import Token

logger = structlog.get_logger(__name__)


class AuthenticationError(Exception):
    """Raised when authentication fails"""

    pass


class AuthService:
    """Service for handling authentication logic"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def authenticate_user(self, email: str, password: str) -> dict[str, Any]:
        """
        Authenticate a user by email and password.

        Args:
            email: User email (UPN)
            password: Plain text password

        Returns:
            User data dictionary

        Raises:
            AuthenticationError: If authentication fails
        """
        # Find user by email (user_principal_name)
        user = await self.user_repo.get_by_email(email)

        if not user:
            logger.warning(
                "authentication_failed", email=email, reason="user_not_found"
            )
            raise AuthenticationError("Invalid credentials")

        # Verify password
        if not hasattr(user, "password_hash") or not user.password_hash:
            logger.warning(
                "authentication_failed", email=email, reason="no_password_hash"
            )
            raise AuthenticationError("Invalid credentials")

        if not verify_password(password, user.password_hash):
            logger.warning(
                "authentication_failed", email=email, reason="invalid_password"
            )
            raise AuthenticationError("Invalid credentials")

        # Check if account is enabled
        if not user.account_enabled:
            logger.warning(
                "authentication_failed", email=email, reason="account_disabled"
            )
            raise AuthenticationError("Account is disabled")

        logger.info("user_authenticated", user_id=str(user.id), email=email)

        return {
            "id": user.id,
            "user_principal_name": user.user_principal_name,
            "tenant_client_id": user.tenant_client_id,
            "display_name": user.display_name,
        }

    async def create_tokens(self, user_data: dict[str, Any]) -> Token:
        """
        Create access and refresh tokens for a user.

        Args:
            user_data: User data dictionary with id, user_principal_name, tenant_client_id

        Returns:
            Token object with access_token and refresh_token
        """
        # Get user's tenants (for now, just the single tenant they belong to)
        tenants = [str(user_data["tenant_client_id"])]

        # Prepare token payload
        token_data = {
            "sub": str(user_data["id"]),
            "email": user_data["user_principal_name"],
            "tenants": tenants,
        }

        # Create tokens
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token({"sub": str(user_data["id"])})

        logger.info(
            "tokens_created", user_id=str(user_data["id"]), tenant_count=len(tenants)
        )

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def refresh_access_token(self, refresh_token: str) -> dict[str, Any]:
        """
        Create a new access token from a refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            Dictionary with new access_token and expires_in

        Raises:
            AuthenticationError: If refresh token is invalid
        """
        try:
            # Decode and verify refresh token
            payload = decode_token(refresh_token)

            # Verify it's a refresh token
            if not verify_token_type(payload, "refresh"):
                logger.warning(
                    "invalid_token_type", expected="refresh", got=payload.get("type")
                )
                raise AuthenticationError("Invalid token type")

            # Extract user_id from token
            user_id_str = payload.get("sub")
            if not user_id_str:
                logger.warning("missing_subject_in_token")
                raise AuthenticationError("Invalid token")

            user_id = UUID(user_id_str)

            # Get user from database
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                logger.warning(
                    "refresh_failed", user_id=user_id_str, reason="user_not_found"
                )
                raise AuthenticationError("User not found")

            # Check if account is enabled
            if not user.account_enabled:
                logger.warning(
                    "refresh_failed", user_id=user_id_str, reason="account_disabled"
                )
                raise AuthenticationError("Account is disabled")

            # Get user's tenants
            tenants = [str(user.tenant_client_id)]

            # Create new access token
            token_data = {
                "sub": str(user.id),
                "email": user.user_principal_name,
                "tenants": tenants,
            }

            access_token = create_access_token(token_data)

            logger.info("access_token_refreshed", user_id=str(user.id))

            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            }

        except JWTError as e:
            logger.warning("refresh_token_invalid", error=str(e))
            raise AuthenticationError("Invalid or expired refresh token")
        except ValueError as e:
            logger.warning("invalid_user_id", error=str(e))
            raise AuthenticationError("Invalid token")
