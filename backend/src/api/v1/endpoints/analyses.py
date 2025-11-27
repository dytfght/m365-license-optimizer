"""
Analysis and Recommendation endpoints
License optimization API
"""
from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....models.user import User
from ....schemas.analysis import (
    AnalysisCreate,
    AnalysisDetailResponse,
    AnalysisList,
    AnalysisResponse,
)
from ....schemas.recommendation import (
    ApplyRecommendationRequest,
    ApplyRecommendationResponse,
    RecommendationResponse,
)
from ....services.analysis_service import AnalysisService
from ....services.recommendation_service import RecommendationService
from ...deps import get_current_user

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/analyses", tags=["analyses"])

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@router.post(
    "/tenants/{tenant_id}/analyses",
    response_model=AnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Launch license optimization analysis",
    description="Run a new license optimization analysis for a tenant. Rate limited to 1 request per minute.",
)
# Rate limit: 1 request per minute
async def create_analysis(
    tenant_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> AnalysisResponse:
    """
    Launch a new optimization analysis for a tenant.

    Args:
        tenant_id: Tenant UUID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Analysis result with summary and recommendations

    Raises:
        HTTPException: If tenant not found or analysis fails
    """
    # Verify user has access to tenant
    if current_user.tenant_client_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this tenant",
        )

    try:
        analysis_service = AnalysisService(db)
        analysis = await analysis_service.run_analysis(tenant_id)

        logger.info(
            "analysis_created_via_api",
            analysis_id=str(analysis.id),
            tenant_id=str(tenant_id),
            user_id=str(current_user.id),
        )

        return AnalysisResponse(
            id=analysis.id,
            tenant_client_id=analysis.tenant_client_id,
            analysis_date=analysis.analysis_date,
            status=analysis.status.value,
            summary=analysis.summary,
            error_message=analysis.error_message,
            created_at=analysis.created_at,
            updated_at=analysis.updated_at,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(
            "analysis_creation_failed",
            tenant_id=str(tenant_id),
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to run analysis",
        )


@router.get(
    "/tenants/{tenant_id}/analyses",
    response_model=AnalysisList,
    status_code=status.HTTP_200_OK,
    summary="List analyses for tenant",
    description="Get list of all analyses for a tenant",
)
async def list_analyses(
    tenant_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = 100,
    offset: int = 0,
) -> AnalysisList:
    """
    List all analyses for a tenant.

    Args:
        tenant_id: Tenant UUID
        limit: Max number of results
        offset: Offset for pagination
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of analyses
    """
    # Verify user has access to tenant
    if current_user.tenant_client_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this tenant",
        )

    analysis_service = AnalysisService(db)
    analyses = await analysis_service.analysis_repo.get_by_tenant(
        tenant_id, limit, offset
    )

    analysis_responses = [
        AnalysisResponse(
            id=analysis.id,
            tenant_client_id=analysis.tenant_client_id,
            analysis_date=analysis.analysis_date,
            status=analysis.status.value,
            summary=analysis.summary,
            error_message=analysis.error_message,
            created_at=analysis.created_at,
            updated_at=analysis.updated_at,
        )
        for analysis in analyses
    ]

    total = await analysis_service.analysis_repo.count_by_tenant(tenant_id)

    return AnalysisList(analyses=analysis_responses, total=total)


@router.get(
    "/analyses/{analysis_id}",
    response_model=AnalysisDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get analysis details",
    description="Get detailed analysis with recommendations",
)
async def get_analysis(
    analysis_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> AnalysisDetailResponse:
    """
    Get analysis details with recommendations.

    Args:
        analysis_id: Analysis UUID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Analysis details with recommendations
    """
    analysis_service = AnalysisService(db)
    analysis = await analysis_service.analysis_repo.get_by_id_with_recommendations(
        analysis_id
    )

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found",
        )

    # Verify user has access to tenant
    if current_user.tenant_client_id != analysis.tenant_client_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this analysis",
        )

    # Build recommendation responses
    recommendation_responses = [
        RecommendationResponse(
            id=rec.id,
            analysis_id=rec.analysis_id,
            user_id=rec.user_id,
            current_sku=rec.current_sku,
            recommended_sku=rec.recommended_sku,
            savings_monthly=rec.savings_monthly,
            reason=rec.reason,
            status=rec.status.value,
            created_at=rec.created_at,
            updated_at=rec.updated_at,
        )
        for rec in analysis.recommendations
    ]

    return AnalysisDetailResponse(
        id=analysis.id,
        tenant_client_id=analysis.tenant_client_id,
        analysis_date=analysis.analysis_date,
        status=analysis.status.value,
        summary=analysis.summary,
        error_message=analysis.error_message,
        created_at=analysis.created_at,
        updated_at=analysis.updated_at,
        recommendations=recommendation_responses,
    )


@router.post(
    "/recommendations/{rec_id}/apply",
    response_model=ApplyRecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Apply or reject recommendation",
    description="Accept or reject a license recommendation",
)
async def apply_recommendation(
    rec_id: UUID,
    request: ApplyRecommendationRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApplyRecommendationResponse:
    """
    Apply or reject a recommendation.

    Args:
        rec_id: Recommendation UUID
        request: Action to perform (accept/reject)
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated recommendation status
    """
    recommendation_service = RecommendationService(db)

    try:
        if request.action == "accept":
            recommendation = await recommendation_service.apply_recommendation(
                rec_id, current_user.id
            )
            message = "Recommendation accepted successfully"
        elif request.action == "reject":
            recommendation = await recommendation_service.reject_recommendation(
                rec_id, current_user.id
            )
            message = "Recommendation rejected successfully"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid action. Must be 'accept' or 'reject'",
            )

        return ApplyRecommendationResponse(
            recommendation_id=recommendation.id,
            status=recommendation.status.value,
            message=message,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(
            "recommendation_apply_failed",
            recommendation_id=str(rec_id),
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to apply recommendation",
        )
