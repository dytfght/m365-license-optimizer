"""
FastAPI dependencies
"""
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..services.tenant_service import TenantService
from ..services.user_sync_service import UserSyncService

# Database session dependency
DBSession = Annotated[AsyncSession, Depends(get_db)]


# Service dependencies
def get_tenant_service(db: DBSession) -> TenantService:
    """Get TenantService instance"""
    return TenantService(db)


def get_user_sync_service(db: DBSession) -> UserSyncService:
    """Get UserSyncService instance"""
    return UserSyncService(db)


TenantServiceDep = Annotated[TenantService, Depends(get_tenant_service)]
UserSyncServiceDep = Annotated[UserSyncService, Depends(get_user_sync_service)]


# BE01: Authentication dependency (simplified for Lot 2)
async def verify_admin_token(
    authorization: Annotated[str | None, Header()] = None
) -> dict:
    """
    Verify admin JWT token (simplified for Lot 2).
    
    In production (Lot 12), this will validate Azure AD tokens.
    For now, accepts any Bearer token for testing.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    scheme, _, token = authorization.partition(" ")
    
    if scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # TODO: Implement proper JWT validation in Lot 12
    # For now, return mock admin user
    return {
        "user_id": "admin-user-id",
        "email": "admin@partner.com",
        "role": "admin",
    }


CurrentAdmin = Annotated[dict, Depends(verify_admin_token)]
