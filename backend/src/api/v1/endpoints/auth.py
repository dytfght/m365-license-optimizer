"""
Authentication endpoints for login and token refresh
"""
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....schemas.token import RefreshTokenRequest, RefreshTokenResponse, Token
from ....services.auth_service import AuthenticationError, AuthService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="User login",
    description="Authenticate user and receive access and refresh tokens",
)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Login endpoint using OAuth2 password flow.

    Args:
        form_data: OAuth2 password request form (username=email, password)
        db: Database session

    Returns:
        Access and refresh tokens

    Raises:
        HTTPException: If authentication fails
    """
    auth_service = AuthService(db)

    try:
        # Authenticate user
        user_data = await auth_service.authenticate_user(
            email=form_data.username,  # OAuth2 uses 'username' field
            password=form_data.password,
        )

        # Create tokens
        tokens = await auth_service.create_tokens(user_data)

        logger.info(
            "user_logged_in",
            user_id=str(user_data["id"]),
            email=user_data["email"],
        )

        return tokens

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Exchange refresh token for new access token",
)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Refresh access token using a valid refresh token.

    Args:
        refresh_data: Refresh token request
        db: Database session

    Returns:
        New access token

    Raises:
        HTTPException: If refresh token is invalid
    """
    auth_service = AuthService(db)

    try:
        # Create new access token
        token_data = await auth_service.refresh_access_token(
            refresh_token=refresh_data.refresh_token
        )

        logger.info("token_refreshed")

        return RefreshTokenResponse(**token_data)

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
