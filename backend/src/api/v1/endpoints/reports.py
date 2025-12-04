"""
API endpoints for report generation and management
"""
from datetime import datetime
from typing import Annotated, Any, Dict, Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....models.user import User
from ....schemas.report import (
    ReportDownloadResponse,
    ReportListResponse,
    ReportResponse,
)
from ....services.reports.report_service import ReportService
from ...deps import get_current_user

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post(
    "/analyses/{analysis_id}/pdf",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate PDF report for analysis",
    description="Generate an executive summary PDF report for a completed analysis",
)
async def generate_pdf_report(
    analysis_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReportResponse:
    """Generate PDF executive summary report"""

    logger.info(
        "generate_pdf_report_requested",
        analysis_id=str(analysis_id),
        user_email=current_user.user_principal_name,
    )

    try:
        # Create report service
        report_service = ReportService(db)

        # Generate PDF report
        report = await report_service.generate_pdf_report(
            analysis_id=analysis_id, generated_by=current_user.user_principal_name
        )

        # Convert to response model using the helper method
        return ReportResponse.from_report(report)

    except ValueError as e:
        logger.warning("analysis_not_found", analysis_id=str(analysis_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis not found: {str(e)}",
        )
    except Exception as e:
        logger.error(
            "failed_to_generate_pdf_report", analysis_id=str(analysis_id), error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF report: {str(e)}",
        )


@router.post(
    "/analyses/{analysis_id}/excel",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate Excel report for analysis",
    description="Generate a detailed Excel report with recommendations and metrics",
)
async def generate_excel_report(
    analysis_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReportResponse:
    """Generate detailed Excel report"""

    logger.info(
        "generate_excel_report_requested",
        analysis_id=str(analysis_id),
        user_email=current_user.user_principal_name,
    )

    try:
        # Create report service
        report_service = ReportService(db)

        # Generate Excel report
        report = await report_service.generate_excel_report(
            analysis_id=analysis_id, generated_by=current_user.user_principal_name
        )

        # Convert to response model using the helper method
        return ReportResponse.from_report(report)

    except ValueError as e:
        logger.warning("analysis_not_found", analysis_id=str(analysis_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis not found: {str(e)}",
        )
    except Exception as e:
        logger.error(
            "failed_to_generate_excel_report",
            analysis_id=str(analysis_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate Excel report: {str(e)}",
        )


@router.get(
    "/analyses/{analysis_id}",
    response_model=ReportListResponse,
    summary="List reports for analysis",
    description="Get all reports generated for a specific analysis",
)
async def list_analysis_reports(
    analysis_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(50, ge=1, le=100, description="Maximum number of reports"),
    offset: int = Query(0, ge=0, description="Number of reports to skip"),
) -> ReportListResponse:
    """List all reports for an analysis"""

    logger.info(
        "list_analysis_reports_requested",
        analysis_id=str(analysis_id),
        limit=limit,
        offset=offset,
        user_email=current_user.user_principal_name,
    )

    try:
        # Create report service
        report_service = ReportService(db)

        # Get reports
        reports = await report_service.get_reports_by_analysis(analysis_id)

        # Apply pagination
        total = len(reports)
        paginated_reports = reports[offset : offset + limit]

        # Convert to response models using the helper method
        report_responses = [
            ReportResponse.from_report(report) for report in paginated_reports
        ]

        return ReportListResponse(
            reports=report_responses, total=total, limit=limit, offset=offset
        )

    except Exception as e:
        logger.error(
            "failed_to_list_analysis_reports",
            analysis_id=str(analysis_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list reports: {str(e)}",
        )


@router.get(
    "/tenants/{tenant_id}",
    response_model=ReportListResponse,
    summary="List reports for tenant",
    description="Get all reports for a specific tenant",
)
async def list_tenant_reports(
    tenant_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(50, ge=1, le=100, description="Maximum number of reports"),
    offset: int = Query(0, ge=0, description="Number of reports to skip"),
    report_type: Optional[str] = Query(
        None, description="Filter by report type (PDF/EXCEL)"
    ),
) -> ReportListResponse:
    """List all reports for a tenant"""

    logger.info(
        "list_tenant_reports_requested",
        tenant_id=str(tenant_id),
        limit=limit,
        offset=offset,
        report_type=report_type,
        user_email=current_user.user_principal_name,
    )

    try:
        # Create report service
        report_service = ReportService(db)

        # Get reports
        reports = await report_service.get_reports_by_tenant(tenant_id)

        # Apply type filter if specified
        if report_type:
            reports = [
                r for r in reports if r.report_type.upper() == report_type.upper()
            ]

        # Apply pagination
        total = len(reports)
        paginated_reports = reports[offset : offset + limit]

        # Convert to response models using the helper method
        report_responses = [
            ReportResponse.from_report(report) for report in paginated_reports
        ]

        return ReportListResponse(
            reports=report_responses, total=total, limit=limit, offset=offset
        )

    except Exception as e:
        logger.error(
            "failed_to_list_tenant_reports", tenant_id=str(tenant_id), error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list reports: {str(e)}",
        )


@router.get(
    "/{report_id}",
    response_model=ReportResponse,
    summary="Get report details",
    description="Get detailed information about a specific report",
)
async def get_report(
    report_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReportResponse:
    """Get report details"""

    logger.info(
        "get_report_requested",
        report_id=str(report_id),
        user_email=current_user.user_principal_name,
    )

    try:
        # Create report service
        report_service = ReportService(db)

        # Get report
        report = await report_service.get_report_by_id(report_id)

        if not report:
            logger.warning("report_not_found", report_id=str(report_id))
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Report not found"
            )

        # Convert to response model using the helper method
        return ReportResponse.from_report(report)

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error("failed_to_get_report", report_id=str(report_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get report: {str(e)}",
        )


@router.get(
    "/{report_id}/download",
    response_model=ReportDownloadResponse,
    summary="Download report file",
    description="Get download URL for a report file",
)
async def download_report(
    report_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReportDownloadResponse:
    """Get download URL for report file"""

    logger.info(
        "download_report_requested",
        report_id=str(report_id),
        user_email=current_user.user_principal_name,
    )

    try:
        # Create report service
        report_service = ReportService(db)

        # Get report
        report = await report_service.get_report_by_id(report_id)

        if not report:
            logger.warning("report_not_found_for_download", report_id=str(report_id))
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Report not found"
            )

        # Check if report is expired
        from datetime import timezone

        if report.expires_at and report.expires_at < datetime.now(timezone.utc):
            logger.warning("report_expired", report_id=str(report_id))
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Report has expired and is no longer available",
            )

        # Return download information
        return ReportDownloadResponse(
            report_id=str(report.id),
            file_name=report.file_name,
            file_size=report.file_size_bytes,
            mime_type=report.mime_type,
            download_url=f"/api/v1/reports/{report_id}/file",  # Actual file endpoint would be implemented separately
            expires_at=report.expires_at,
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(
            "failed_to_get_report_download", report_id=str(report_id), error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get download information: {str(e)}",
        )


@router.get(
    "/{report_id}/file",
    summary="Serve report file",
    description="Download the actual report file (PDF or Excel)",
)
async def serve_report_file(
    report_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Serve the actual report file for download"""
    from fastapi.responses import FileResponse
    import os

    logger.info(
        "serve_report_file_requested",
        report_id=str(report_id),
        user_email=current_user.user_principal_name,
    )

    try:
        # Create report service
        report_service = ReportService(db)

        # Get report
        report = await report_service.get_report_by_id(report_id)

        if not report:
            logger.warning("report_not_found_for_file", report_id=str(report_id))
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Report not found"
            )

        # Check if report is expired
        from datetime import timezone

        if report.expires_at and report.expires_at < datetime.now(timezone.utc):
            logger.warning("report_expired_for_file", report_id=str(report_id))
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Report has expired and is no longer available",
            )

        # Check if file exists
        if not os.path.exists(report.file_path):
            logger.error("report_file_not_found", file_path=report.file_path)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report file not found on server",
            )

        logger.info(
            "serving_report_file",
            report_id=str(report_id),
            file_name=report.file_name,
            mime_type=report.mime_type,
        )

        return FileResponse(
            path=report.file_path,
            filename=report.file_name,
            media_type=report.mime_type,
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(
            "failed_to_serve_report_file", report_id=str(report_id), error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to serve report file: {str(e)}",
        )


@router.delete(
    "/{report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete report",
    description="Soft delete a report (mark as expired)",
)
async def delete_report(
    report_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Soft delete a report"""

    logger.info(
        "delete_report_requested",
        report_id=str(report_id),
        user_email=current_user.user_principal_name,
    )

    try:
        # Create report service
        report_service = ReportService(db)

        # Delete report
        success = await report_service.delete_report(report_id)

        if not success:
            logger.warning("report_not_found_for_deletion", report_id=str(report_id))
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Report not found"
            )

        logger.info("report_deleted_successfully", report_id=str(report_id))

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error("failed_to_delete_report", report_id=str(report_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete report: {str(e)}",
        )


@router.post(
    "/cleanup",
    summary="Clean up expired reports",
    description="Remove reports that have exceeded their TTL",
)
async def cleanup_expired_reports(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Dict[str, Any]:
    """Clean up expired reports"""

    logger.info(
        "cleanup_expired_reports_requested", user_email=current_user.user_principal_name
    )

    try:
        # Create report service
        report_service = ReportService(db)

        # Cleanup expired reports
        deleted_count = await report_service.cleanup_expired_reports()

        logger.info("cleanup_completed", deleted_count=deleted_count)

        return {
            "message": "Cleanup completed successfully",
            "deleted_reports": deleted_count,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error("failed_to_cleanup_expired_reports", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup expired reports: {str(e)}",
        )
