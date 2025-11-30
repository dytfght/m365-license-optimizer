"""
Analytics API endpoints
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....api.deps import get_current_user
from ....core.database import get_db
from ....models.user import User
from ....schemas.analytics import (
    AnalyticsMetricCreate,
    AnalyticsMetricFilter,
    AnalyticsMetricListResponse,
    AnalyticsMetricResponse,
    AnalyticsMetricUpdate,
    AnalyticsSnapshotCreate,
    AnalyticsSnapshotFilter,
    AnalyticsSnapshotListResponse,
    AnalyticsSnapshotResponse,
    AnalyticsSnapshotUpdate,
    AnalyticsSummaryResponse,
    DashboardKPIsResponse,
)
from ....services.analytics_service import AnalyticsService

router = APIRouter()


@router.post(
    "/metrics",
    response_model=AnalyticsMetricResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_metric(
    metric_data: AnalyticsMetricCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalyticsMetricResponse:
    """Create a new analytics metric"""
    analytics_service = AnalyticsService(db)

    # Verify user has access to the tenant
    if str(metric_data.tenant_client_id) != str(current_user.tenant_client_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to create metrics for this tenant",
        )

    return await analytics_service.create_metric(metric_data)


@router.get("/metrics", response_model=AnalyticsMetricListResponse)
async def get_metrics(
    tenant_client_id: Optional[UUID] = Query(
        None, description="Filter by tenant client ID"
    ),
    metric_type: Optional[str] = Query(None, description="Filter by metric type"),
    metric_name: Optional[str] = Query(
        None, description="Filter by metric name (partial match)"
    ),
    period_start: Optional[datetime] = Query(
        None, description="Filter by period start date (ISO format)"
    ),
    period_end: Optional[datetime] = Query(
        None, description="Filter by period end date (ISO format)"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalyticsMetricListResponse:
    """Get analytics metrics with filtering"""
    analytics_service = AnalyticsService(db)

    # Use current user's tenant if not specified
    if not tenant_client_id:
        tenant_client_id = current_user.tenant_client_id

    # Verify user has access to the tenant
    if str(tenant_client_id) != str(current_user.tenant_client_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view metrics for this tenant",
        )

    # Create filter
    filters = AnalyticsMetricFilter(
        tenant_client_id=tenant_client_id,
        metric_type=metric_type,
        metric_name=metric_name,
        period_start=period_start,
        period_end=period_end,
    )

    # Get filtered metrics
    metrics = await analytics_service.filter_metrics(filters)

    # Apply pagination
    total = len(metrics)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_metrics = metrics[start_idx:end_idx]

    return AnalyticsMetricListResponse(
        metrics=paginated_metrics,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/metrics/{metric_id}", response_model=AnalyticsMetricResponse)
async def get_metric(
    metric_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalyticsMetricResponse:
    """Get a specific metric by ID"""
    analytics_service = AnalyticsService(db)

    metric = await analytics_service.get_metric(metric_id)
    if not metric:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Metric not found"
        )

    # Verify user has access to the tenant
    if str(metric.tenant_client_id) != str(current_user.tenant_client_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this metric",
        )

    return metric


@router.put("/metrics/{metric_id}", response_model=AnalyticsMetricResponse)
async def update_metric(
    metric_id: UUID,
    update_data: AnalyticsMetricUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalyticsMetricResponse:
    """Update a specific metric"""
    analytics_service = AnalyticsService(db)

    # First get the metric to verify ownership
    existing_metric = await analytics_service.get_metric(metric_id)
    if not existing_metric:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Metric not found"
        )

    # Verify user has access to the tenant
    if str(existing_metric.tenant_client_id) != str(current_user.tenant_client_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this metric",
        )

    # Update the metric
    updated_metric = await analytics_service.update_metric(metric_id, update_data)
    if not updated_metric:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Metric not found after update",
        )

    return updated_metric


@router.delete("/metrics/{metric_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_metric(
    metric_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a specific metric"""
    analytics_service = AnalyticsService(db)

    # First get the metric to verify ownership
    existing_metric = await analytics_service.get_metric(metric_id)
    if not existing_metric:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Metric not found"
        )

    # Verify user has access to the tenant
    if str(existing_metric.tenant_client_id) != str(current_user.tenant_client_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this metric",
        )

    success = await analytics_service.delete_metric(metric_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Metric not found"
        )


# Snapshot endpoints
@router.post(
    "/snapshots",
    response_model=AnalyticsSnapshotResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_snapshot(
    snapshot_data: AnalyticsSnapshotCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalyticsSnapshotResponse:
    """Create a new analytics snapshot"""
    analytics_service = AnalyticsService(db)

    # Verify user has access to the tenant
    if str(snapshot_data.tenant_client_id) != str(current_user.tenant_client_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to create snapshots for this tenant",
        )

    return await analytics_service.create_snapshot(snapshot_data)


@router.get("/snapshots", response_model=AnalyticsSnapshotListResponse)
async def get_snapshots(
    tenant_client_id: Optional[UUID] = Query(
        None, description="Filter by tenant client ID"
    ),
    snapshot_type: Optional[str] = Query(None, description="Filter by snapshot type"),
    snapshot_date: Optional[datetime] = Query(
        None, description="Filter by snapshot date (from, ISO format)"
    ),
    snapshot_date_to: Optional[datetime] = Query(
        None, description="Filter by snapshot date (to, ISO format)"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalyticsSnapshotListResponse:
    """Get analytics snapshots with filtering"""
    analytics_service = AnalyticsService(db)

    # Use current user's tenant if not specified
    if not tenant_client_id:
        tenant_client_id = current_user.tenant_client_id

    # Verify user has access to the tenant
    if str(tenant_client_id) != str(current_user.tenant_client_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view snapshots for this tenant",
        )

    # Create filter
    filters = AnalyticsSnapshotFilter(
        tenant_client_id=tenant_client_id,
        snapshot_type=snapshot_type,
        snapshot_date=snapshot_date,
        snapshot_date_to=snapshot_date_to,
    )

    # Get filtered snapshots
    snapshots = await analytics_service.filter_snapshots(filters)

    # Apply pagination
    total = len(snapshots)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_snapshots = snapshots[start_idx:end_idx]

    return AnalyticsSnapshotListResponse(
        snapshots=paginated_snapshots,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/snapshots/{snapshot_id}", response_model=AnalyticsSnapshotResponse)
async def get_snapshot(
    snapshot_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalyticsSnapshotResponse:
    """Get a specific snapshot by ID"""
    analytics_service = AnalyticsService(db)

    snapshot = await analytics_service.get_snapshot(snapshot_id)
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Snapshot not found"
        )

    # Verify user has access to the tenant
    if str(snapshot.tenant_client_id) != str(current_user.tenant_client_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this snapshot",
        )

    return snapshot


@router.put("/snapshots/{snapshot_id}", response_model=AnalyticsSnapshotResponse)
async def update_snapshot(
    snapshot_id: UUID,
    update_data: AnalyticsSnapshotUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalyticsSnapshotResponse:
    """Update a specific snapshot"""
    analytics_service = AnalyticsService(db)

    # First get the snapshot to verify ownership
    existing_snapshot = await analytics_service.get_snapshot(snapshot_id)
    if not existing_snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Snapshot not found"
        )

    # Verify user has access to the tenant
    if str(existing_snapshot.tenant_client_id) != str(current_user.tenant_client_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this snapshot",
        )

    # Update the snapshot
    updated_snapshot = await analytics_service.update_snapshot(snapshot_id, update_data)
    if not updated_snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Snapshot not found after update",
        )

    return updated_snapshot


@router.delete("/snapshots/{snapshot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_snapshot(
    snapshot_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a specific snapshot"""
    analytics_service = AnalyticsService(db)

    # First get the snapshot to verify ownership
    existing_snapshot = await analytics_service.get_snapshot(snapshot_id)
    if not existing_snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Snapshot not found"
        )

    # Verify user has access to the tenant
    if str(existing_snapshot.tenant_client_id) != str(current_user.tenant_client_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this snapshot",
        )

    success = await analytics_service.delete_snapshot(snapshot_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Snapshot not found"
        )


# Summary and dashboard endpoints
@router.get("/summary", response_model=AnalyticsSummaryResponse)
async def get_analytics_summary(
    tenant_client_id: Optional[UUID] = Query(None, description="Tenant client ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalyticsSummaryResponse:
    """Get analytics summary for a tenant"""
    analytics_service = AnalyticsService(db)

    # Use current user's tenant if not specified
    if not tenant_client_id:
        tenant_client_id = current_user.tenant_client_id

    # Verify user has access to the tenant
    if str(tenant_client_id) != str(current_user.tenant_client_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view analytics for this tenant",
        )

    return await analytics_service.get_tenant_analytics_summary(tenant_client_id)


@router.get("/dashboard/kpis", response_model=DashboardKPIsResponse)
async def get_dashboard_kpis(
    tenant_client_id: Optional[UUID] = Query(None, description="Tenant client ID"),
    period_days: int = Query(30, ge=7, le=365, description="Period in days"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardKPIsResponse:
    """Get KPIs for dashboard display"""
    analytics_service = AnalyticsService(db)

    # Use current user's tenant if not specified
    if not tenant_client_id:
        tenant_client_id = current_user.tenant_client_id

    # Verify user has access to the tenant
    if str(tenant_client_id) != str(current_user.tenant_client_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view KPIs for this tenant",
        )

    return await analytics_service.get_dashboard_kpis(tenant_client_id, period_days)
