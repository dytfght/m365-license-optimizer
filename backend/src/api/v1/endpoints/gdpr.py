"""
GDPR API Endpoints for LOT 10
Handles consent, data export, and right to erasure.
"""
from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ....services.gdpr_service import GdprService
from ...deps import get_current_user, get_db

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/gdpr", tags=["GDPR"])


# ============================================
# Pydantic Schemas
# ============================================


class ConsentRequest(BaseModel):
    """Request to record GDPR consent."""

    consent_given: bool = True


class ConsentResponse(BaseModel):
    """Response for consent recording."""

    tenant_id: str
    gdpr_consent: bool
    gdpr_consent_date: str | None
    message: str


class DataExportResponse(BaseModel):
    """Response metadata for data export."""

    user_id: str
    export_date: str
    format: str = "json"


class DeletionResponse(BaseModel):
    """Response for data deletion."""

    user_id: str
    action: str
    timestamp: str
    data_affected: dict[str, str]


# ============================================
# Endpoints
# ============================================


@router.post(
    "/consent/{tenant_id}",
    response_model=ConsentResponse,
    summary="Record GDPR Consent",
    description="Record GDPR consent for a tenant (Article 7).",
)
async def record_consent(
    tenant_id: UUID,
    request: ConsentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ConsentResponse:
    """
    Record GDPR consent for a tenant.

    Args:
        tenant_id: Tenant UUID
        request: Consent request body
        db: Database session
        current_user: Authenticated user

    Returns:
        Consent confirmation
    """
    try:
        service = GdprService(db)
        tenant = await service.record_consent(tenant_id, request.consent_given)

        logger.info(
            "gdpr_consent_api",
            tenant_id=str(tenant_id),
            consent=request.consent_given,
            user=current_user.get("user_principal_name"),
        )

        return ConsentResponse(
            tenant_id=str(tenant.id),
            gdpr_consent=tenant.gdpr_consent,
            gdpr_consent_date=(
                tenant.gdpr_consent_date.isoformat()
                if tenant.gdpr_consent_date
                else None
            ),
            message="Consent recorded successfully",
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("gdpr_consent_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record consent",
        )


@router.get(
    "/consent/{tenant_id}",
    summary="Check GDPR Consent",
    description="Check if a tenant has given GDPR consent.",
)
async def check_consent(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Check GDPR consent status for a tenant.

    Args:
        tenant_id: Tenant UUID
        db: Database session
        current_user: Authenticated user

    Returns:
        Consent status
    """
    service = GdprService(db)
    has_consent = await service.check_consent(tenant_id)

    return {
        "tenant_id": str(tenant_id),
        "has_consent": has_consent,
    }


@router.get(
    "/export/{user_id}",
    summary="Export User Data",
    description="Export all personal data for a user (Article 20 - Data Portability).",
)
async def export_user_data(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Export all personal data for a user.

    Args:
        user_id: User UUID
        db: Database session
        current_user: Authenticated user

    Returns:
        User data in JSON format
    """
    try:
        service = GdprService(db)
        data = await service.export_user_data(user_id)

        logger.info(
            "gdpr_export_api",
            user_id=str(user_id),
            requester=current_user.get("user_principal_name"),
        )

        return data

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("gdpr_export_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export data",
        )


@router.delete(
    "/delete/{user_id}",
    response_model=DeletionResponse,
    summary="Delete User Data",
    description="Delete or anonymize all personal data for a user (Article 17 - Right to Erasure).",
)
async def delete_user_data(
    user_id: UUID,
    anonymize: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> DeletionResponse:
    """
    Delete or anonymize all personal data for a user.

    Args:
        user_id: User UUID
        anonymize: If True, anonymize instead of delete
        db: Database session
        current_user: Authenticated user

    Returns:
        Deletion summary
    """
    try:
        service = GdprService(db)
        result = await service.delete_user_data(user_id, anonymize=anonymize)

        logger.info(
            "gdpr_delete_api",
            user_id=str(user_id),
            action=result["action"],
            requester=current_user.get("user_principal_name"),
        )

        return DeletionResponse(
            user_id=result["user_id"],
            action=result["action"],
            timestamp=result["timestamp"],
            data_affected=result["data_affected"],
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("gdpr_delete_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete data",
        )


@router.post(
    "/admin/registry",
    summary="Generate GDPR Registry PDF",
    description="Generate the GDPR processing activities registry (Article 30).",
)
async def generate_registry(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> Response:
    """
    Generate GDPR processing activities registry PDF.

    Args:
        db: Database session
        current_user: Authenticated user

    Returns:
        PDF file
    """
    try:
        service = GdprService(db)
        pdf_content = await service.generate_registry_pdf()

        logger.info(
            "gdpr_registry_generated",
            requester=current_user.get("user_principal_name"),
            size_bytes=len(pdf_content),
        )

        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=gdpr_registry.pdf"
            },
        )

    except Exception as e:
        logger.error("gdpr_registry_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate registry",
        )
