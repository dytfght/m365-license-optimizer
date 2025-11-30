"""
Analytics service for business logic
"""
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..models.analytics import (
    AnalyticsMetric,
    AnalyticsSnapshot,
    MetricType,
    SnapshotType,
)
from ..repositories.analytics_repository import (
    AnalyticsMetricRepository,
    AnalyticsSnapshotRepository,
)
from ..schemas.analytics import (
    AnalyticsMetricCreate,
    AnalyticsMetricFilter,
    AnalyticsMetricResponse,
    AnalyticsSnapshotCreate,
    AnalyticsSnapshotFilter,
    AnalyticsSnapshotResponse,
    AnalyticsSummaryResponse,
    DashboardKPIsResponse,
    KPIResponse,
)


class AnalyticsService:
    """Service for analytics operations"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.metric_repo = AnalyticsMetricRepository(db)
        self.snapshot_repo = AnalyticsSnapshotRepository(db)

    async def create_metric(
        self, metric_data: AnalyticsMetricCreate
    ) -> AnalyticsMetricResponse:
        """Create a new analytics metric"""
        metric = await self.metric_repo.create(metric_data)
        return AnalyticsMetricResponse.model_validate(metric)

    async def create_snapshot(
        self, snapshot_data: AnalyticsSnapshotCreate
    ) -> AnalyticsSnapshotResponse:
        """Create a new analytics snapshot with optional hash calculation"""
        # Calculate data hash if not provided
        if not snapshot_data.data_hash and snapshot_data.snapshot_data:
            data_str = json.dumps(snapshot_data.snapshot_data, sort_keys=True)
            snapshot_data.data_hash = hashlib.sha256(data_str.encode()).hexdigest()

        snapshot = await self.snapshot_repo.create(snapshot_data)
        return AnalyticsSnapshotResponse.model_validate(snapshot)

    async def get_metric(self, metric_id: UUID) -> Optional[AnalyticsMetricResponse]:
        """Get a specific metric by ID"""
        metric = await self.metric_repo.get(metric_id)
        return AnalyticsMetricResponse.model_validate(metric) if metric else None

    async def get_snapshot(
        self, snapshot_id: UUID
    ) -> Optional[AnalyticsSnapshotResponse]:
        """Get a specific snapshot by ID"""
        snapshot = await self.snapshot_repo.get(snapshot_id)
        return AnalyticsSnapshotResponse.model_validate(snapshot) if snapshot else None

    async def update_metric(
        self, metric_id: UUID, update_data: AnalyticsMetricCreate
    ) -> Optional[AnalyticsMetricResponse]:
        """Update an existing metric"""
        metric = await self.metric_repo.update(metric_id, update_data)
        return AnalyticsMetricResponse.model_validate(metric) if metric else None

    async def update_snapshot(
        self, snapshot_id: UUID, update_data: AnalyticsSnapshotCreate
    ) -> Optional[AnalyticsSnapshotResponse]:
        """Update an existing snapshot"""
        # Recalculate hash if data changed
        if update_data.snapshot_data and not update_data.data_hash:
            data_str = json.dumps(update_data.snapshot_data, sort_keys=True)
            update_data.data_hash = hashlib.sha256(data_str.encode()).hexdigest()

        snapshot = await self.snapshot_repo.update(snapshot_id, update_data)
        return AnalyticsSnapshotResponse.model_validate(snapshot) if snapshot else None

    async def delete_metric(self, metric_id: UUID) -> bool:
        """Delete a metric"""
        return await self.metric_repo.delete(metric_id)

    async def delete_snapshot(self, snapshot_id: UUID) -> bool:
        """Delete a snapshot"""
        return await self.snapshot_repo.delete(snapshot_id)

    async def get_metrics_by_tenant(
        self,
        tenant_client_id: UUID,
        metric_type: Optional[MetricType] = None,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> Sequence[AnalyticsMetricResponse]:
        """Get metrics for a specific tenant"""
        if metric_type:
            metrics = await self.metric_repo.get_by_tenant_and_type(
                tenant_client_id, metric_type, period_start
            )
            return [
                AnalyticsMetricResponse.model_validate(m) for m in [metrics] if metrics
            ]
        elif period_start and period_end:
            metrics = await self.metric_repo.get_metrics_by_period(
                tenant_client_id, period_start, period_end
            )
        else:
            # Get all metrics for tenant
            filter_data = AnalyticsMetricFilter(tenant_client_id=tenant_client_id)
            metrics = await self.metric_repo.filter_metrics(filter_data)

        return [AnalyticsMetricResponse.model_validate(m) for m in metrics]

    async def get_snapshots_by_tenant(
        self,
        tenant_client_id: UUID,
        snapshot_type: Optional[SnapshotType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Sequence[AnalyticsSnapshotResponse]:
        """Get snapshots for a specific tenant"""
        if snapshot_type and not (start_date and end_date):
            snapshot = await self.snapshot_repo.get_by_tenant_and_type(
                tenant_client_id, snapshot_type
            )
            return [
                AnalyticsSnapshotResponse.model_validate(s)
                for s in [snapshot]
                if snapshot
            ]
        elif start_date and end_date:
            snapshots = await self.snapshot_repo.get_snapshots_by_date_range(
                tenant_client_id,
                start_date,
                end_date,
                [snapshot_type] if snapshot_type else None,
            )
        else:
            # Get all snapshots for tenant
            filter_data = AnalyticsSnapshotFilter(tenant_client_id=tenant_client_id)
            if snapshot_type:
                filter_data.snapshot_type = snapshot_type
            snapshots = await self.snapshot_repo.filter_snapshots(filter_data)

        return [AnalyticsSnapshotResponse.model_validate(s) for s in snapshots]

    async def filter_metrics(
        self, filters: AnalyticsMetricFilter
    ) -> Sequence[AnalyticsMetricResponse]:
        """Filter metrics based on criteria"""
        metrics = await self.metric_repo.filter_metrics(filters)
        return [AnalyticsMetricResponse.model_validate(m) for m in metrics]

    async def filter_snapshots(
        self, filters: AnalyticsSnapshotFilter
    ) -> Sequence[AnalyticsSnapshotResponse]:
        """Filter snapshots based on criteria"""
        snapshots = await self.snapshot_repo.filter_snapshots(filters)
        return [AnalyticsSnapshotResponse.model_validate(s) for s in snapshots]

    async def get_tenant_analytics_summary(
        self, tenant_client_id: UUID
    ) -> AnalyticsSummaryResponse:
        """Get analytics summary for a tenant"""
        metric_summary = await self.metric_repo.get_metric_summary(tenant_client_id)
        snapshot_summary = await self.snapshot_repo.get_snapshot_summary(
            tenant_client_id
        )

        # Get available metric and snapshot types
        from sqlalchemy import distinct, select

        metric_types_query = await self.metric_repo.session.execute(
            select(distinct(AnalyticsMetric.metric_type)).where(
                AnalyticsMetric.tenant_client_id == tenant_client_id
            )
        )
        available_metric_types = [row[0] for row in metric_types_query.all()]

        snapshot_types_query = await self.snapshot_repo.session.execute(
            select(distinct(AnalyticsSnapshot.snapshot_type)).where(
                AnalyticsSnapshot.tenant_client_id == tenant_client_id
            )
        )
        available_snapshot_types = [row[0] for row in snapshot_types_query.all()]

        # Determine date range
        earliest_date = None
        latest_date = None

        if metric_summary["earliest_period"] and snapshot_summary["earliest_date"]:
            earliest_date = min(
                metric_summary["earliest_period"], snapshot_summary["earliest_date"]
            )
        elif metric_summary["earliest_period"]:
            earliest_date = metric_summary["earliest_period"]
        elif snapshot_summary["earliest_date"]:
            earliest_date = snapshot_summary["earliest_date"]

        if metric_summary["latest_period"] and snapshot_summary["latest_date"]:
            latest_date = max(
                metric_summary["latest_period"], snapshot_summary["latest_date"]
            )
        elif metric_summary["latest_period"]:
            latest_date = metric_summary["latest_period"]
        elif snapshot_summary["latest_date"]:
            latest_date = snapshot_summary["latest_date"]

        return AnalyticsSummaryResponse(
            tenant_client_id=tenant_client_id,
            total_metrics=metric_summary["total_metrics"],
            total_snapshots=snapshot_summary["total_snapshots"],
            metric_types=available_metric_types,
            snapshot_types=available_snapshot_types,
            date_range={"start": earliest_date, "end": latest_date}
            if earliest_date and latest_date
            else {},
            last_updated=latest_date or datetime.utcnow(),
        )

    async def get_dashboard_kpis(
        self,
        tenant_client_id: UUID,
        period_days: int = 30,
    ) -> DashboardKPIsResponse:
        """Get KPIs for dashboard display"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)

        # Get previous period for comparison
        prev_start_date = start_date - timedelta(days=period_days)
        prev_end_date = start_date

        # Get current period metrics
        current_metrics = await self.metric_repo.get_metrics_by_period(
            tenant_client_id, start_date, end_date
        )

        # Get previous period metrics for trend calculation
        previous_metrics = await self.metric_repo.get_metrics_by_period(
            tenant_client_id, prev_start_date, prev_end_date
        )

        # Create KPIs with trend information
        kpis = []

        for metric in current_metrics:
            # Find corresponding previous metric
            prev_metric = next(
                (
                    m
                    for m in previous_metrics
                    if m.metric_type == metric.metric_type
                    and m.metric_name == metric.metric_name
                ),
                None,
            )

            # Calculate trend
            trend = None
            change_percentage = None

            if (
                prev_metric
                and prev_metric.value.replace(".", "").isdigit()
                and metric.value.replace(".", "").isdigit()
            ):
                try:
                    current_value = float(metric.value)
                    prev_value = float(prev_metric.value)

                    if prev_value != 0:
                        change_percentage = (
                            (current_value - prev_value) / prev_value
                        ) * 100

                        if change_percentage > 5:
                            trend = "up"
                        elif change_percentage < -5:
                            trend = "down"
                        else:
                            trend = "stable"
                except (ValueError, TypeError):
                    pass

            kpi = KPIResponse(
                metric_type=metric.metric_type,
                metric_name=metric.metric_name,
                value=metric.value,
                unit=metric.unit,
                period_start=metric.period_start,
                period_end=metric.period_end,
                trend=trend,
                change_percentage=change_percentage,
            )
            kpis.append(kpi)

        return DashboardKPIsResponse(
            kpis=kpis,
            period_start=start_date,
            period_end=end_date,
            generated_at=datetime.utcnow(),
        )

    async def create_license_optimization_metrics(
        self,
        tenant_client_id: UUID,
        period_start: datetime,
        period_end: datetime,
        license_utilization: float,
        total_cost: float,
        potential_savings: float,
        efficiency_score: float,
    ) -> list[AnalyticsMetricResponse]:
        """Create metrics for license optimization analysis"""
        metrics_data = [
            AnalyticsMetricCreate(
                tenant_client_id=tenant_client_id,
                metric_type=MetricType.LICENSE_UTILIZATION,
                metric_name="License Utilization Rate",
                value=f"{license_utilization:.2f}",
                period_start=period_start,
                period_end=period_end,
                unit="%",
                context={"calculation_method": "active_users / total_licenses"},
            ),
            AnalyticsMetricCreate(
                tenant_client_id=tenant_client_id,
                metric_type=MetricType.LICENSE_COST,
                metric_name="Total License Cost",
                value=f"{total_cost:.2f}",
                period_start=period_start,
                period_end=period_end,
                unit="EUR",
                context={"currency": "EUR", "period": "monthly"},
            ),
            AnalyticsMetricCreate(
                tenant_client_id=tenant_client_id,
                metric_type=MetricType.LICENSE_SAVINGS,
                metric_name="Potential Monthly Savings",
                value=f"{potential_savings:.2f}",
                period_start=period_start,
                period_end=period_end,
                unit="EUR",
                context={"currency": "EUR", "savings_type": "optimization"},
            ),
            AnalyticsMetricCreate(
                tenant_client_id=tenant_client_id,
                metric_type=MetricType.LICENSE_EFFICIENCY,
                metric_name="License Efficiency Score",
                value=f"{efficiency_score:.2f}",
                period_start=period_start,
                period_end=period_end,
                unit="/10",
                context={
                    "scoring_method": "utilization + cost_effectiveness + compliance"
                },
            ),
        ]

        created_metrics = []
        for metric_data in metrics_data:
            metric = await self.create_metric(metric_data)
            created_metrics.append(metric)

        return created_metrics

    async def create_user_activity_metrics(
        self,
        tenant_client_id: UUID,
        period_start: datetime,
        period_end: datetime,
        active_users: int,
        inactive_users: int,
        disabled_users: int,
        guest_users: int,
    ) -> list[AnalyticsMetricResponse]:
        """Create metrics for user activity analysis"""
        total_users = active_users + inactive_users + disabled_users + guest_users

        metrics_data = [
            AnalyticsMetricCreate(
                tenant_client_id=tenant_client_id,
                metric_type=MetricType.ACTIVE_USERS,
                metric_name="Active Users",
                value=str(active_users),
                period_start=period_start,
                period_end=period_end,
                unit="users",
                context={"total_users": total_users, "activity_threshold": "30_days"},
            ),
            AnalyticsMetricCreate(
                tenant_client_id=tenant_client_id,
                metric_type=MetricType.INACTIVE_USERS,
                metric_name="Inactive Users",
                value=str(inactive_users),
                period_start=period_start,
                period_end=period_end,
                unit="users",
                context={"total_users": total_users, "inactivity_threshold": "30_days"},
            ),
            AnalyticsMetricCreate(
                tenant_client_id=tenant_client_id,
                metric_type=MetricType.DISABLED_USERS,
                metric_name="Disabled Users",
                value=str(disabled_users),
                period_start=period_start,
                period_end=period_end,
                unit="users",
                context={"total_users": total_users},
            ),
            AnalyticsMetricCreate(
                tenant_client_id=tenant_client_id,
                metric_type=MetricType.GUEST_USERS,
                metric_name="Guest Users",
                value=str(guest_users),
                period_start=period_start,
                period_end=period_end,
                unit="users",
                context={"total_users": total_users},
            ),
        ]

        created_metrics = []
        for metric_data in metrics_data:
            metric = await self.create_metric(metric_data)
            created_metrics.append(metric)

        return created_metrics

    async def cleanup_old_data(
        self,
        tenant_client_id: UUID,
        metrics_keep_days: int = 90,
        snapshots_keep_days: int = 365,
    ) -> dict:
        """Clean up old analytics data"""
        metrics_deleted = await self.metric_repo.delete_old_metrics(
            tenant_client_id, metrics_keep_days
        )
        snapshots_deleted = await self.snapshot_repo.delete_old_snapshots(
            tenant_client_id, snapshots_keep_days
        )

        return {
            "metrics_deleted": metrics_deleted,
            "snapshots_deleted": snapshots_deleted,
            "total_deleted": metrics_deleted + snapshots_deleted,
        }
