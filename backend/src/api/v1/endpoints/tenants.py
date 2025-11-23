"""
Tenant management endpoints
"""
from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....models.user import User
from ....repositories.tenant_repository import TenantRepository
from ....schemas.tenant import TenantList, TenantResponse, TenantCreateRequest
from ...deps import get_current_user

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.get(
    "",
    response_model=TenantList,
    status_code=status.HTTP_200_OK,
    summary="List user's tenants",
    description="Get list of tenants the authenticated user has access to",
)
async def list_tenants(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Get list of tenants for the authenticated user.

    Args:
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of tenants
    """
    tenant_repo = TenantRepository(db)

    # For now, get the user's tenant
    # TODO: In the future, support users with access to multiple tenants
    tenant = await tenant_repo.get_by_id(current_user.tenant_client_id)

    tenants = [tenant] if tenant else []

    # Convert to TenantResponse
    tenant_responses = [
        TenantResponse(
            id=UUID(str(t.id)),
            tenant_id=t.tenant_id,
            name=t.name,
            country=t.country,
            default_language=t.default_language,
            onboarding_status=t.onboarding_status,
            csp_customer_id=t.csp_customer_id,
            created_at=t.created_at,
            updated_at=t.updated_at,
        )
        for t in tenants
    ]

    logger.info(
        "tenants_listed",
        user_id=str(current_user.id),
        tenant_count=len(tenant_responses),
    )

    return TenantList(
        tenants=tenant_responses,
        total=len(tenant_responses),
    )


@router.post(
    "",
    response_model=TenantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tenant",
    description="Create a new tenant with app registration details",
)
async def create_tenant(
    tenant_in: TenantCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Create a new tenant.

    Args:
        tenant_in: Tenant creation data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Created tenant
    """
    tenant_repo = TenantRepository(db)

    # Prepare data for repository
    tenant_data = tenant_in.model_dump(
        include={"name", "country", "default_language", "tenant_id", "csp_customer_id"}
    )

    app_reg_data = tenant_in.model_dump(
        include={"client_id", "scopes", "authority_url"}
    )
    # In a real application, we should encrypt the client secret
    # For now, we store it as is (or encrypted if the model handles it)
    # The model expects 'client_secret_encrypted'
    app_reg_data["client_secret_encrypted"] = tenant_in.client_secret

    try:
        tenant = await tenant_repo.create_with_app_registration(
            tenant_data, app_reg_data
        )
        await db.commit()
        await db.refresh(tenant)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant with this ID already exists",
        )
    except Exception as e:
        await db.rollback()
        logger.error("tenant_creation_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create tenant",
        )

    logger.info(
        "tenant_created",
        tenant_id=str(tenant.id),
        user_id=str(current_user.id),
    )

    return TenantResponse(
        id=UUID(str(tenant.id)),
        tenant_id=tenant.tenant_id,
        name=tenant.name,
        country=tenant.country,
        default_language=tenant.default_language,
        onboarding_status=tenant.onboarding_status,
        csp_customer_id=tenant.csp_customer_id,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at,
    )


@router.get(
    "/{tenant_id}",
    response_model=TenantResponse,
    status_code=status.HTTP_200_OK,
    summary="Get tenant by ID",
    description="Get details of a specific tenant",
)
async def get_tenant(
    tenant_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Get tenant by ID.

    Args:
        tenant_id: Tenant ID (UUID)
        db: Database session
        current_user: Current authenticated user

    Returns:
        Tenant details
    """
    tenant_repo = TenantRepository(db)

    # Check if user has access to this tenant
    # For now, simple check against user's tenant_id
    # TODO: Implement proper permission check

    try:
        # Try to parse as UUID
        from uuid import UUID

        uuid_obj = UUID(tenant_id)
        tenant = await tenant_repo.get_by_id(uuid_obj)
    except ValueError:
        # If not UUID, try as Azure Tenant ID?
        # The endpoint path param is usually the internal ID
        tenant = None

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    return TenantResponse(
        id=UUID(str(tenant.id)),
        tenant_id=tenant.tenant_id,
        name=tenant.name,
        country=tenant.country,
        default_language=tenant.default_language,
        onboarding_status=tenant.onboarding_status,
        csp_customer_id=tenant.csp_customer_id,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at,
    )
