"""
Admin SKU Mapping endpoints
SKU mapping and add-on management API
"""
from typing import Annotated, Dict, List, Optional, Union
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.deps import get_current_admin_user
from src.core.database import get_db
from src.models.user import User
from src.repositories.addon_compatibility_repository import AddonCompatibilityRepository
from src.schemas.sku_mapping import (
    AddonCompatibilityCreate,
    AddonCompatibilityResponse,
    AddonCompatibilityUpdate,
    AddonValidationRequest,
    AddonValidationResponse,
    SkuMappingSummary,
)
from src.services.addon_validator import AddonValidator
from src.services.partner_center_addons_service import PartnerCenterAddonsService
from src.services.sku_mapping_service import SkuMappingService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/admin/sku-mapping", tags=["admin", "sku-mapping"])

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@router.get(
    "/summary",
    response_model=SkuMappingSummary,
    status_code=status.HTTP_200_OK,
    summary="Get SKU mapping summary",
    description="Get summary statistics of SKU mappings and add-on compatibility",
)
async def get_sku_mapping_summary(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_admin_user)],
) -> SkuMappingSummary:
    """
    Get SKU mapping summary statistics.

    Args:
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        SKU mapping summary statistics
    """
    try:
        sku_service = SkuMappingService(db)
        summary = await sku_service.get_sku_mapping_summary()

        return SkuMappingSummary(
            total_partner_center_products=summary["total_partner_center_products"],
            total_compatibility_mappings=summary["total_compatibility_mappings"],
            active_mappings=summary["active_mappings"],
            service_type_distribution=summary["service_type_distribution"],
            addon_category_distribution=summary["addon_category_distribution"],
            mapping_coverage=summary["mapping_coverage"],
        )

    except Exception as e:
        logger.error(
            "sku_mapping_summary_failed",
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get SKU mapping summary",
        )


@router.post(
    "/sync/products",
    response_model=Dict[str, int],
    status_code=status.HTTP_200_OK,
    summary="Sync Partner Center products",
    description="Synchronize products from Microsoft Partner Center",
)
async def sync_partner_center_products(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_admin_user)],
    country: str = Query("US", description="Country code for Partner Center"),
    currency: str = Query("USD", description="Currency for Partner Center"),
) -> Dict[str, int]:
    """
    Sync products from Microsoft Partner Center.

    Args:
        db: Database session
        current_user: Current authenticated admin user
        country: Country code
        currency: Currency code

    Returns:
        Sync statistics with created and updated counts
    """
    try:
        pc_service = PartnerCenterAddonsService(db)
        created, updated = await pc_service.sync_partner_center_products()

        logger.info(
            "partner_center_products_synced_via_api",
            created=created,
            updated=updated,
            user_id=str(current_user.id),
        )

        return {"created": created, "updated": updated}

    except Exception as e:
        logger.error(
            "partner_center_sync_failed",
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync Partner Center products",
        )


@router.post(
    "/sync/compatibility",
    response_model=Dict[str, int],
    status_code=status.HTTP_200_OK,
    summary="Sync add-on compatibility rules",
    description="Synchronize add-on compatibility rules from Microsoft Partner Center",
)
async def sync_addon_compatibility_rules(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_admin_user)],
) -> Dict[str, int]:
    """
    Sync add-on compatibility rules from Microsoft Partner Center.

    Args:
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        Sync statistics with created and updated counts
    """
    try:
        pc_service = PartnerCenterAddonsService(db)
        created, updated = await pc_service.sync_addon_compatibility_rules()

        logger.info(
            "addon_compatibility_rules_synced_via_api",
            created=created,
            updated=updated,
            user_id=str(current_user.id),
        )

        return {"created": created, "updated": updated}

    except Exception as e:
        logger.error(
            "addon_compatibility_sync_failed",
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync add-on compatibility rules",
        )


@router.get(
    "/compatible-addons/{base_sku_id}",
    response_model=List[Dict[str, Union[str, int, bool, None]]],
    status_code=status.HTTP_200_OK,
    summary="Get compatible add-ons",
    description="Get all compatible add-ons for a base SKU",
)
async def get_compatible_addons(
    base_sku_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_admin_user)],
    service_type: Optional[str] = Query(None, description="Filter by service type"),
    addon_category: Optional[str] = Query(
        None, description="Filter by add-on category"
    ),
) -> List[Dict[str, Union[str, int, bool, None]]]:
    """
    Get compatible add-ons for a base SKU.

    Args:
        base_sku_id: Base SKU ID from Partner Center
        db: Database session
        current_user: Current authenticated admin user
        service_type: Optional service type filter
        addon_category: Optional add-on category filter

    Returns:
        List of compatible add-ons with details
    """
    try:
        sku_service = SkuMappingService(db)
        compatible_addons = await sku_service.get_compatible_addons(
            base_sku_id, service_type, addon_category
        )

        return compatible_addons

    except Exception as e:
        logger.error(
            "get_compatible_addons_failed",
            base_sku_id=base_sku_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get compatible add-ons",
        )


@router.post(
    "/validate-addon",
    response_model=AddonValidationResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate add-on compatibility",
    description="Validate if an add-on is compatible with a base SKU",
)
async def validate_addon_compatibility(
    request: AddonValidationRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_admin_user)],
) -> AddonValidationResponse:
    """
    Validate add-on compatibility.

    Args:
        request: Validation request with add-on details
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        Validation result with success status and errors
    """
    try:
        validator = AddonValidator(db)
        is_valid, errors = await validator.validate_addon_compatibility(
            addon_sku_id=request.addon_sku_id,
            base_sku_id=request.base_sku_id,
            quantity=request.quantity,
            tenant_id=request.tenant_id,
            domain_name=request.domain_name,
        )

        return AddonValidationResponse(
            is_valid=is_valid,
            errors=errors,
            addon_sku_id=request.addon_sku_id,
            base_sku_id=request.base_sku_id,
            quantity=request.quantity,
            validation_requirements={},  # Provide default or actual requirements if available
        )

    except Exception as e:
        logger.error(
            "addon_validation_failed",
            addon_sku_id=request.addon_sku_id,
            base_sku_id=request.base_sku_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate add-on compatibility",
        )


@router.get(
    "/compatibility-mappings",
    response_model=List[AddonCompatibilityResponse],
    status_code=status.HTTP_200_OK,
    summary="List compatibility mappings",
    description="List all add-on compatibility mappings with optional filters",
)
async def list_compatibility_mappings(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_admin_user)],
    addon_sku_id: Optional[str] = Query(None, description="Filter by add-on SKU ID"),
    base_sku_id: Optional[str] = Query(None, description="Filter by base SKU ID"),
    service_type: Optional[str] = Query(None, description="Filter by service type"),
    addon_category: Optional[str] = Query(
        None, description="Filter by add-on category"
    ),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
) -> List[AddonCompatibilityResponse]:
    """
    List compatibility mappings with optional filters.

    Args:
        db: Database session
        current_user: Current authenticated admin user
        addon_sku_id: Optional add-on SKU filter
        base_sku_id: Optional base SKU filter
        service_type: Optional service type filter
        addon_category: Optional add-on category filter
        is_active: Optional active status filter
        limit: Maximum number of results
        offset: Offset for pagination

    Returns:
        List of compatibility mappings
    """
    try:
        addon_repo = AddonCompatibilityRepository(db)

        # Apply filters
        if addon_sku_id:
            mappings = await addon_repo.get_by_addon_sku(addon_sku_id)
        elif base_sku_id:
            mappings = await addon_repo.get_by_base_sku(base_sku_id)
        elif service_type:
            mappings = await addon_repo.get_by_service_type(service_type)
        elif addon_category:
            mappings = await addon_repo.get_by_addon_category(addon_category)
        elif is_active is not None:
            if is_active:
                mappings = await addon_repo.get_active_mappings()
            else:
                # Get inactive mappings by filtering all mappings
                all_mappings = await addon_repo.get_all(limit=1000)
                mappings = [m for m in all_mappings if not m.is_active]
        else:
            mappings = await addon_repo.get_all(limit, offset)

        # Apply additional filters manually if needed
        if service_type and not any([addon_sku_id, base_sku_id]):
            mappings = [m for m in mappings if m.service_type == service_type]

        if addon_category and not any([addon_sku_id, base_sku_id]):
            mappings = [m for m in mappings if m.addon_category == addon_category]

        if is_active is not None and not any(
            [addon_sku_id, base_sku_id, service_type, addon_category]
        ):
            mappings = [m for m in mappings if m.is_active == is_active]

        # Apply pagination manually if we did custom filtering
        if any([service_type, addon_category, is_active is not None]) and not any(
            [addon_sku_id, base_sku_id]
        ):
            mappings = mappings[offset : offset + limit]

        return [
            AddonCompatibilityResponse(
                id=UUID(str(mapping.id)),
                addon_sku_id=mapping.addon_sku_id,
                addon_product_id=mapping.addon_product_id,
                base_sku_id=mapping.base_sku_id,
                base_product_id=mapping.base_product_id,
                service_type=mapping.service_type,
                addon_category=mapping.addon_category,
                min_quantity=mapping.min_quantity,
                max_quantity=mapping.max_quantity,
                quantity_multiplier=mapping.quantity_multiplier,
                requires_domain_validation=mapping.requires_domain_validation,
                requires_tenant_validation=mapping.requires_tenant_validation,
                is_active=mapping.is_active,
                effective_date=mapping.effective_date,
                expiration_date=mapping.expiration_date,
                description=mapping.description,
                notes=mapping.notes,
                created_at=mapping.created_at,
                updated_at=mapping.updated_at,
            )
            for mapping in mappings
        ]

    except Exception as e:
        logger.error(
            "list_compatibility_mappings_failed",
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list compatibility mappings",
        )


@router.post(
    "/compatibility-mappings",
    response_model=AddonCompatibilityResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create compatibility mapping",
    description="Create a new add-on compatibility mapping",
)
async def create_compatibility_mapping(
    request: AddonCompatibilityCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_admin_user)],
) -> AddonCompatibilityResponse:
    """
    Create a new compatibility mapping.

    Args:
        request: Mapping creation request
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        Created compatibility mapping
    """
    try:
        sku_service = SkuMappingService(db)
        mapping = await sku_service.create_mapping(**request.model_dump())

        logger.info(
            "compatibility_mapping_created_via_api",
            mapping_id=str(mapping.id),
            addon_sku_id=mapping.addon_sku_id,
            base_sku_id=mapping.base_sku_id,
            user_id=str(current_user.id),
        )

        return AddonCompatibilityResponse(
            id=UUID(str(mapping.id)),
            addon_sku_id=mapping.addon_sku_id,
            addon_product_id=mapping.addon_product_id,
            base_sku_id=mapping.base_sku_id,
            base_product_id=mapping.base_product_id,
            service_type=mapping.service_type,
            addon_category=mapping.addon_category,
            min_quantity=mapping.min_quantity,
            max_quantity=mapping.max_quantity,
            quantity_multiplier=mapping.quantity_multiplier,
            requires_domain_validation=mapping.requires_domain_validation,
            requires_tenant_validation=mapping.requires_tenant_validation,
            is_active=mapping.is_active,
            effective_date=mapping.effective_date,
            expiration_date=mapping.expiration_date,
            description=mapping.description,
            notes=mapping.notes,
            created_at=mapping.created_at,
            updated_at=mapping.updated_at,
        )

    except Exception as e:
        logger.error(
            "create_compatibility_mapping_failed",
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create compatibility mapping",
        )


@router.put(
    "/compatibility-mappings/{mapping_id}",
    response_model=AddonCompatibilityResponse,
    status_code=status.HTTP_200_OK,
    summary="Update compatibility mapping",
    description="Update an existing add-on compatibility mapping",
)
async def update_compatibility_mapping(
    mapping_id: UUID,
    request: AddonCompatibilityUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_admin_user)],
) -> AddonCompatibilityResponse:
    """
    Update a compatibility mapping.

    Args:
        mapping_id: Mapping UUID
        request: Mapping update request
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        Updated compatibility mapping
    """
    try:
        sku_service = SkuMappingService(db)
        mapping = await sku_service.update_mapping(
            mapping_id, **request.model_dump(exclude_unset=True)
        )

        if not mapping:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Compatibility mapping not found",
            )

        logger.info(
            "compatibility_mapping_updated_via_api",
            mapping_id=str(mapping_id),
            user_id=str(current_user.id),
        )

        return AddonCompatibilityResponse(
            id=UUID(str(mapping.id)),
            addon_sku_id=mapping.addon_sku_id,
            addon_product_id=mapping.addon_product_id,
            base_sku_id=mapping.base_sku_id,
            base_product_id=mapping.base_product_id,
            service_type=mapping.service_type,
            addon_category=mapping.addon_category,
            min_quantity=mapping.min_quantity,
            max_quantity=mapping.max_quantity,
            quantity_multiplier=mapping.quantity_multiplier,
            requires_domain_validation=mapping.requires_domain_validation,
            requires_tenant_validation=mapping.requires_tenant_validation,
            is_active=mapping.is_active,
            effective_date=mapping.effective_date,
            expiration_date=mapping.expiration_date,
            description=mapping.description,
            notes=mapping.notes,
            created_at=mapping.created_at,
            updated_at=mapping.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "update_compatibility_mapping_failed",
            mapping_id=str(mapping_id),
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update compatibility mapping",
        )


@router.delete(
    "/compatibility-mappings/{mapping_id}",
    response_model=Dict[str, str],
    status_code=status.HTTP_200_OK,
    summary="Delete compatibility mapping",
    description="Delete an add-on compatibility mapping",
)
async def delete_compatibility_mapping(
    mapping_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_admin_user)],
) -> Dict[str, str]:
    """
    Delete a compatibility mapping.

    Args:
        mapping_id: Mapping UUID
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        Success message
    """
    try:
        sku_service = SkuMappingService(db)
        success = await sku_service.delete_mapping(mapping_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Compatibility mapping not found",
            )

        logger.info(
            "compatibility_mapping_deleted_via_api",
            mapping_id=str(mapping_id),
            user_id=str(current_user.id),
        )

        return {"message": "Compatibility mapping deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "delete_compatibility_mapping_failed",
            mapping_id=str(mapping_id),
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete compatibility mapping",
        )


@router.get(
    "/recommendations/{base_sku_id}",
    response_model=List[Dict[str, Union[str, int, bool, float]]],
    status_code=status.HTTP_200_OK,
    summary="Get add-on recommendations",
    description="Get add-on recommendations for a base SKU based on usage patterns",
)
async def get_addon_recommendations(
    base_sku_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_admin_user)],
    current_addons: Optional[str] = Query(
        None, description="Comma-separated list of current add-on SKUs"
    ),
    tenant_size: str = Query(
        "medium", description="Tenant size (small, medium, large, enterprise)"
    ),
) -> List[Dict[str, Union[str, int, bool, float]]]:
    """
    Get add-on recommendations for a base SKU.

    Args:
        base_sku_id: Base SKU ID from Partner Center
        db: Database session
        current_user: Current authenticated admin user
        current_addons: Comma-separated list of current add-on SKUs
        tenant_size: Tenant size category

    Returns:
        List of add-on recommendations
    """
    try:
        pc_service = PartnerCenterAddonsService(db)

        current_addons_list = []
        if current_addons:
            current_addons_list = [addon.strip() for addon in current_addons.split(",")]

        recommendations = await pc_service.get_addon_recommendations(
            base_sku_id, current_addons_list, tenant_size
        )

        return recommendations

    except Exception as e:
        logger.error(
            "get_addon_recommendations_failed",
            base_sku_id=base_sku_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get add-on recommendations",
        )
