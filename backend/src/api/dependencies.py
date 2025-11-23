"""
FastAPI dependencies
"""
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.database import get_db, get_redis
from ..repositories.license_repository import LicenseRepository
from ..repositories.usage_metrics_repository import UsageMetricsRepository
from ..repositories.user_repository import UserRepository
from ..services.encryption_service import EncryptionService
from ..services.graph_auth_service import GraphAuthService
from ..services.graph_service import GraphService
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


# LOT4: Microsoft Graph dependencies

# Singleton encryption service
_encryption_service: EncryptionService | None = None


def get_encryption_service() -> EncryptionService:
    """Get or create encryption service singleton"""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService(settings.ENCRYPTION_KEY)
    return _encryption_service


async def get_graph_auth_service(
    db: DBSession,
    encryption: Annotated[EncryptionService, Depends(get_encryption_service)],
) -> GraphAuthService:
    """Get GraphAuthService instance"""
    redis = await get_redis()
    return GraphAuthService(db, redis, encryption)


async def get_graph_service(
    auth_service: Annotated[GraphAuthService, Depends(get_graph_auth_service)],
) -> GraphService:
    """Get GraphService instance"""
    return GraphService(auth_service)


def get_user_repository(db: DBSession) -> UserRepository:
    """Get UserRepository instance"""
    return UserRepository(db)


def get_license_repository(db: DBSession) -> LicenseRepository:
    """Get LicenseRepository instance"""
    return LicenseRepository(db)


def get_usage_metrics_repository(db: DBSession) -> UsageMetricsRepository:
    """Get UsageMetricsRepository instance"""
    return UsageMetricsRepository(db)


# Type aliases for LOT4
EncryptionServiceDep = Annotated[EncryptionService, Depends(get_encryption_service)]
GraphAuthServiceDep = Annotated[GraphAuthService, Depends(get_graph_auth_service)]
GraphServiceDep = Annotated[GraphService, Depends(get_graph_service)]
UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]
LicenseRepositoryDep = Annotated[LicenseRepository, Depends(get_license_repository)]
UsageMetricsRepositoryDep = Annotated[
    UsageMetricsRepository, Depends(get_usage_metrics_repository)
]


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
CurrentUser = CurrentAdmin  # Alias for endpoints that use CurrentUser naming
