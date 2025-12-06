"""
Logs API Endpoints for LOT 10
Admin endpoints for viewing and managing audit logs.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ....services.logging_service import LoggingService
from ...deps import get_current_user, get_db

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/admin/logs", tags=["Admin - Logs"])


# ============================================
# Pydantic Schemas
# ============================================


class LogEntry(BaseModel):
    """Log entry response model."""

    id: str
    created_at: str | None
    level: str
    message: str
    endpoint: str | None
    method: str | None
    request_id: str | None
    user_id: str | None
    tenant_id: str | None
    ip_address: str | None
    response_status: int | None
    duration_ms: int | None
    action: str | None


class LogListResponse(BaseModel):
    """Paginated log list response."""

    logs: list[LogEntry]
    total: int
    page: int
    page_size: int
    has_more: bool


class PurgeResponse(BaseModel):
    """Response for log purge operation."""

    deleted_count: int
    retention_days: int
    message: str


class LogStatistics(BaseModel):
    """Log statistics response."""

    period_days: int
    total_logs: int
    by_level: dict[str, int]
    error_count: int
    error_rate_percent: float


# ============================================
# Endpoints
# ============================================


@router.get(
    "",
    response_model=LogListResponse,
    summary="List Audit Logs",
    description="Retrieve paginated and filtered audit logs.",
)
async def list_logs(
    level: Optional[str] = Query(None, description="Filter by log level"),
    tenant_id: Optional[UUID] = Query(None, description="Filter by tenant"),
    user_id: Optional[UUID] = Query(None, description="Filter by user"),
    endpoint: Optional[str] = Query(None, description="Filter by endpoint (partial match)"),
    action: Optional[str] = Query(None, description="Filter by action category"),
    start_date: Optional[datetime] = Query(None, description="Filter from date"),
    end_date: Optional[datetime] = Query(None, description="Filter to date"),
    min_status: Optional[int] = Query(None, description="Minimum HTTP status"),
    max_status: Optional[int] = Query(None, description="Maximum HTTP status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> LogListResponse:
    """
    List audit logs with optional filters.

    Args:
        level: Log level filter
        tenant_id: Tenant UUID filter
        user_id: User UUID filter
        endpoint: Endpoint partial match filter
        action: Action category filter
        start_date: Start date filter
        end_date: End date filter
        min_status: Minimum HTTP status filter
        max_status: Maximum HTTP status filter
        page: Page number (1-indexed)
        page_size: Number of items per page
        db: Database session
        current_user: Authenticated user

    Returns:
        Paginated log list
    """
    try:
        service = LoggingService(db)
        offset = (page - 1) * page_size

        logs, total = await service.get_logs(
            level=level,
            tenant_id=tenant_id,
            user_id=user_id,
            endpoint=endpoint,
            action=action,
            start_date=start_date,
            end_date=end_date,
            min_status=min_status,
            max_status=max_status,
            limit=page_size,
            offset=offset,
        )

        log_entries = [
            LogEntry(
                id=str(log.id),
                created_at=log.created_at.isoformat() if log.created_at else None,
                level=log.level,
                message=log.message,
                endpoint=log.endpoint,
                method=log.method,
                request_id=log.request_id,
                user_id=str(log.user_id) if log.user_id else None,
                tenant_id=str(log.tenant_id) if log.tenant_id else None,
                ip_address=log.ip_address,
                response_status=log.response_status,
                duration_ms=log.duration_ms,
                action=log.action,
            )
            for log in logs
        ]

        return LogListResponse(
            logs=log_entries,
            total=total,
            page=page,
            page_size=page_size,
            has_more=(offset + len(logs)) < total,
        )

    except Exception as e:
        logger.error("list_logs_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve logs",
        )


@router.get(
    "/{log_id}",
    response_model=LogEntry,
    summary="Get Log Details",
    description="Retrieve a specific log entry by ID.",
)
async def get_log(
    log_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> LogEntry:
    """
    Get a specific log entry.

    Args:
        log_id: Log UUID
        db: Database session
        current_user: Authenticated user

    Returns:
        Log entry details
    """
    try:
        service = LoggingService(db)
        log = await service.get_log_by_id(log_id)

        if not log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Log {log_id} not found",
            )

        return LogEntry(
            id=str(log.id),
            created_at=log.created_at.isoformat() if log.created_at else None,
            level=log.level,
            message=log.message,
            endpoint=log.endpoint,
            method=log.method,
            request_id=log.request_id,
            user_id=str(log.user_id) if log.user_id else None,
            tenant_id=str(log.tenant_id) if log.tenant_id else None,
            ip_address=log.ip_address,
            response_status=log.response_status,
            duration_ms=log.duration_ms,
            action=log.action,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_log_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve log",
        )


@router.post(
    "/purge",
    response_model=PurgeResponse,
    summary="Purge Old Logs",
    description="Delete logs older than the retention period (default 90 days for GDPR).",
)
async def purge_logs(
    days: Optional[int] = Query(None, description="Retention days (default 90)"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> PurgeResponse:
    """
    Purge logs older than the specified retention period.

    Args:
        days: Number of days to retain (default from settings)
        db: Database session
        current_user: Authenticated user

    Returns:
        Purge summary
    """
    try:
        service = LoggingService(db)
        deleted_count = await service.purge_old_logs(days=days)

        retention_days = days or 90

        logger.info(
            "logs_purged_api",
            deleted_count=deleted_count,
            retention_days=retention_days,
            requester=current_user.get("email"),
        )

        return PurgeResponse(
            deleted_count=deleted_count,
            retention_days=retention_days,
            message=f"Purged {deleted_count} logs older than {retention_days} days",
        )

    except Exception as e:
        logger.error("purge_logs_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to purge logs",
        )


@router.get(
    "/statistics/summary",
    response_model=LogStatistics,
    summary="Get Log Statistics",
    description="Get log statistics for monitoring.",
)
async def get_statistics(
    tenant_id: Optional[UUID] = Query(None, description="Filter by tenant"),
    days: int = Query(7, ge=1, le=365, description="Analysis period in days"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> LogStatistics:
    """
    Get log statistics for monitoring.

    Args:
        tenant_id: Optional tenant filter
        days: Number of days to analyze
        db: Database session
        current_user: Authenticated user

    Returns:
        Log statistics
    """
    try:
        service = LoggingService(db)
        stats = await service.get_log_statistics(tenant_id=tenant_id, days=days)

        return LogStatistics(**stats)

    except Exception as e:
        logger.error("get_statistics_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get statistics",
        )
