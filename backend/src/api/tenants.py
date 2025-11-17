"""
BE02: API endpoints for tenant management
BE03: API endpoint for triggering analysis (placeholder)
"""
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status

from .dependencies import CurrentAdmin, TenantServiceDep, UserSyncServiceDep
from .schemas import (
    TenantCreate,
    TenantDetailResponse,
    TenantResponse,
    UserSyncResponse,
    ValidationResponse,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.get("", response_model=list[TenantResponse])
async def list_tenants(
    admin: CurrentAdmin,
    tenant_service: TenantServiceDep,
):
    """
    List all tenant clients.
    
    Requires admin authentication.
    """
    logger.info("list_tenants_requested", admin_user=admin["email"])
    
    tenants = await tenant_service.get_all_tenants()
    
    return tenants


@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant_data: TenantCreate,
    admin: CurrentAdmin,
    tenant_service: TenantServiceDep,
):
    """
    Create a new tenant client with app registration.
    
    Requires admin authentication.
    """
    logger.info(
        "create_tenant_requested",
        admin_user=admin["email"],
        tenant_name=tenant_data.name
    )
    
    try:
        tenant = await tenant_service.create_tenant(
            name=tenant_data.name,
            tenant_id=tenant_data.tenant_id,
            country=tenant_data.country,
            client_id=tenant_data.client_id,
            client_secret=tenant_data.client_secret,
            scopes=tenant_data.scopes,
            default_language=tenant_data.default_language,
            csp_customer_id=tenant_data.csp_customer_id,
        )
        
        return tenant
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{tenant_id}", response_model=TenantDetailResponse)
async def get_tenant(
    tenant_id: UUID,
    admin: CurrentAdmin,
    tenant_service: TenantServiceDep,
):
    """
    Get tenant details by ID.
    
    Requires admin authentication.
    """
    logger.info(
        "get_tenant_requested",
        admin_user=admin["email"],
        tenant_id=str(tenant_id)
    )
    
    try:
        tenant = await tenant_service.get_tenant_by_id(tenant_id)
        return tenant
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{tenant_id}/validate", response_model=ValidationResponse)
async def validate_tenant_credentials(
    tenant_id: UUID,
    admin: CurrentAdmin,
    tenant_service: TenantServiceDep,
):
    """
    Validate tenant app registration credentials.
    
    Attempts to get a Graph API token and call the API to verify permissions.
    """
    logger.info(
        "validate_tenant_requested",
        admin_user=admin["email"],
        tenant_id=str(tenant_id)
    )
    
    try:
        result = await tenant_service.validate_tenant_credentials(tenant_id)
        return result
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{tenant_id}/users/sync", response_model=UserSyncResponse)
async def sync_tenant_users(
    tenant_id: UUID,
    admin: CurrentAdmin,
    user_sync_service: UserSyncServiceDep,
):
    """
    Sync users from Microsoft Graph for a tenant.
    
    Fetches all users and their assigned licenses, and upserts them in the database.
    """
    logger.info(
        "sync_users_requested",
        admin_user=admin["email"],
        tenant_id=str(tenant_id)
    )
    
    try:
        result = await user_sync_service.sync_users(tenant_id)
        return result
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(
            "sync_users_failed",
            tenant_id=str(tenant_id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"User sync failed: {str(e)}"
        )


# BE03: Placeholder for analysis trigger (will be implemented in later lots)
@router.post("/{tenant_id}/analyze")
async def trigger_analysis(
    tenant_id: UUID,
    admin: CurrentAdmin,
):
    """
    Trigger license analysis for a tenant (placeholder for Lot 9+).
    
    Returns HTTP 501 Not Implemented for now.
    """
    logger.info(
        "analyze_requested",
        admin_user=admin["email"],
        tenant_id=str(tenant_id)
    )
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Analysis feature will be implemented in Lot 9"
    )
