"""
Users endpoints
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....api.deps import get_current_user
from ....core.database import get_db
from ....models.user import User
from ....schemas.language import LanguageResponse, LanguageUpdate
from ....schemas.user import UserResponse
from ....services.i18n_service import i18n_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Get current user.
    """
    return current_user


@router.put("/{user_id}/language", response_model=LanguageResponse)
async def update_user_language(
    user_id: UUID,
    language_data: LanguageUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LanguageResponse:
    """
    Update user language preference
    """
    # Check if user is updating their own language or has admin rights
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=i18n_service.translate("auth.unauthorized", current_user.language),
        )

    # Update language
    current_user.language = language_data.language
    await db.commit()
    await db.refresh(current_user)

    return LanguageResponse(
        language=current_user.language,
        available_languages=["en", "fr"]
    )


@router.get("/{user_id}/language", response_model=LanguageResponse)
async def get_user_language(
    user_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
) -> LanguageResponse:
    """
    Get user language preference
    """
    # Verify user can access this information
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=i18n_service.translate("auth.unauthorized", current_user.language),
        )

    return LanguageResponse(
        language=current_user.language,
        available_languages=["en", "fr"]
    )
