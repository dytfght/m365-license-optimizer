"""
Users endpoints
"""
from typing import Annotated

from fastapi import APIRouter, Depends

from ....api.deps import get_current_user
from ....models.user import User
from ....schemas.user import UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Get current user.
    """
    return current_user
