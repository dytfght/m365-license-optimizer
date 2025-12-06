"""
Analytics repository for database operations
"""
from datetime import datetime
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.analytics import (
    AnalyticsMetric,
    AnalyticsSnapshot,
    MetricType,
    SnapshotType,
)
from ..schemas.analytics import (
    AnalyticsMetricCreate,
    AnalyticsMetricFilter,
    AnalyticsMetricUpdate,
    AnalyticsSnapshotCreate,
    AnalyticsSnapshotFilter,
    AnalyticsSnapshotUpdate,
)
from .base import BaseRepository


class AnalyticsMetricRepository(BaseRepository[AnalyticsMetric]):
    """Repository for AnalyticsMetric operations"""

    def __init__(self, db: AsyncSession):
        super().__init__(AnalyticsMetric, db)

    async def create(self, data: AnalyticsMetricCreate) -> AnalyticsMetric:  # type: ignore[override]
        """Create a new analytics metric"""
        metric = AnalyticsMetric(**data.model_dump())
        self.session.add(metric)
        await self.session.flush()
        await self.session.refresh(metric)
        return metric

    async def update(  # type: ignore[override]
        self, metric: AnalyticsMetric, data: AnalyticsMetricUpdate
    ) -> AnalyticsMetric:
        """Update an existing analytics metric"""
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(metric, field, value)

        await self.session.flush()
        await self.session.refresh(metric)
        return metric

    async def get_by_tenant_and_type(
        self,
        tenant_client_id: UUID,
        metric_type: MetricType,
        period_start: Optional[datetime] = None,
    ) -> Optional[AnalyticsMetric]:
        """Get metric by tenant and type with optional period filter"""
        query = select(AnalyticsMetric).where(
            AnalyticsMetric.tenant_client_id == tenant_client_id,
            AnalyticsMetric.metric_type == metric_type,
        )

        if period_start:
            query = query.where(AnalyticsMetric.period_start >= period_start)

        query = query.order_by(AnalyticsMetric.period_start.desc())
        result = await self.session.execute(query.limit(1))
        return result.scalar_one_or_none()

    async def get_metrics_by_period(
        self,
        tenant_client_id: UUID,
        period_start: datetime,
        period_end: datetime,
        metric_types: Optional[list[MetricType]] = None,
    ) -> Sequence[AnalyticsMetric]:
        """Get metrics for a specific period"""
        query = select(AnalyticsMetric).where(
            AnalyticsMetric.tenant_client_id == tenant_client_id,
            AnalyticsMetric.period_start >= period_start,
            AnalyticsMetric.period_end <= period_end,
        )

        if metric_types:
            query = query.where(AnalyticsMetric.metric_type.in_(metric_types))

        query = query.order_by(
            AnalyticsMetric.period_start.desc(), AnalyticsMetric.metric_type
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_latest_metrics_by_type(
        self, tenant_client_id: UUID, metric_types: list[MetricType]
    ) -> Sequence[AnalyticsMetric]:
        """Get the latest metric of each type for a tenant"""
        # Subquery to get the latest period_start for each metric_type
        subquery = (
            select(
                AnalyticsMetric.metric_type,
                func.max(AnalyticsMetric.period_start).label("latest_period_start"),
            )
            .where(
                AnalyticsMetric.tenant_client_id == tenant_client_id,
                AnalyticsMetric.metric_type.in_(metric_types),
            )
            .group_by(AnalyticsMetric.metric_type)
            .subquery()
        )

        # Main query to get the actual metrics
        query = select(AnalyticsMetric).join(
            subquery,
            and_(
                AnalyticsMetric.metric_type == subquery.c.metric_type,
                AnalyticsMetric.period_start == subquery.c.latest_period_start,
            ),
        ).where(AnalyticsMetric.tenant_client_id == tenant_client_id)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def filter_metrics(
        self, filters: AnalyticsMetricFilter
    ) -> Sequence[AnalyticsMetric]:
        """Filter metrics based on provided criteria"""
        query = select(AnalyticsMetric)

        if filters.tenant_client_id:
            query = query.where(
                AnalyticsMetric.tenant_client_id == filters.tenant_client_id
            )

        if filters.metric_type:
            query = query.where(AnalyticsMetric.metric_type == filters.metric_type)

        if filters.period_start:
            query = query.where(AnalyticsMetric.period_start >= filters.period_start)

        if filters.period_end:
            query = query.where(AnalyticsMetric.period_end <= filters.period_end)

        if filters.metric_name:
            query = query.where(
                AnalyticsMetric.metric_name.ilike(f"%{filters.metric_name}%")
            )

        query = query.order_by(
            AnalyticsMetric.period_start.desc(), AnalyticsMetric.metric_type
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def delete_old_metrics(
        self, tenant_client_id: UUID, keep_days: int = 90
    ) -> int:
        """Delete metrics older than specified days"""
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=keep_days)

        # Find count first
        count_query = select(func.count()).where(
            AnalyticsMetric.tenant_client_id == tenant_client_id,
            AnalyticsMetric.period_end < cutoff_date,
        )
        result = await self.session.execute(count_query)
        count = result.scalar() or 0

        if count > 0:
            # Execute delete
            from sqlalchemy import delete
            stmt = delete(AnalyticsMetric).where(
                AnalyticsMetric.tenant_client_id == tenant_client_id,
                AnalyticsMetric.period_end < cutoff_date,
            )
            await self.session.execute(stmt)
            await self.session.commit()

        return count

    async def get_metric_summary(self, tenant_client_id: UUID) -> dict:
        """Get summary statistics for metrics"""
        query = select(
            func.count(AnalyticsMetric.id).label("total_metrics"),
            func.count(func.distinct(AnalyticsMetric.metric_type)).label(
                "metric_types"
            ),
            func.min(AnalyticsMetric.period_start).label("earliest_period"),
            func.max(AnalyticsMetric.period_end).label("latest_period"),
        ).where(AnalyticsMetric.tenant_client_id == tenant_client_id)

        result = await self.session.execute(query)
        row = result.one()

        return {
            "total_metrics": row.total_metrics,
            "metric_types": row.metric_types,
            "earliest_period": row.earliest_period,
            "latest_period": row.latest_period,
        }


class AnalyticsSnapshotRepository(BaseRepository[AnalyticsSnapshot]):
    """Repository for AnalyticsSnapshot operations"""

    def __init__(self, db: AsyncSession):
        super().__init__(AnalyticsSnapshot, db)

    async def create(self, data: AnalyticsSnapshotCreate) -> AnalyticsSnapshot:  # type: ignore[override]
        """Create a new analytics snapshot"""
        snapshot = AnalyticsSnapshot(**data.model_dump())
        self.session.add(snapshot)
        await self.session.flush()
        await self.session.refresh(snapshot)
        return snapshot

    async def update(  # type: ignore[override]
        self, snapshot: AnalyticsSnapshot, data: AnalyticsSnapshotUpdate
    ) -> AnalyticsSnapshot:
        """Update an existing analytics snapshot"""
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(snapshot, field, value)

        await self.session.flush()
        await self.session.refresh(snapshot)
        return snapshot

    async def get_by_tenant_and_type(
        self,
        tenant_client_id: UUID,
        snapshot_type: SnapshotType,
        snapshot_date: Optional[datetime] = None,
    ) -> Optional[AnalyticsSnapshot]:
        """Get snapshot by tenant and type with optional date filter"""
        query = select(AnalyticsSnapshot).where(
            AnalyticsSnapshot.tenant_client_id == tenant_client_id,
            AnalyticsSnapshot.snapshot_type == snapshot_type,
        )

        if snapshot_date:
            # Get the snapshot closest to the requested date
            query = query.order_by(
                func.abs(
                    func.extract(
                        "epoch", AnalyticsSnapshot.snapshot_date - snapshot_date
                    )
                )
            )
        else:
            # Get the most recent snapshot
            query = query.order_by(AnalyticsSnapshot.snapshot_date.desc())

        result = await self.session.execute(query.limit(1))
        return result.scalar_one_or_none()

    async def get_snapshots_by_date_range(
        self,
        tenant_client_id: UUID,
        start_date: datetime,
        end_date: datetime,
        snapshot_types: Optional[list[SnapshotType]] = None,
    ) -> Sequence[AnalyticsSnapshot]:
        """Get snapshots for a specific date range"""
        query = select(AnalyticsSnapshot).where(
            AnalyticsSnapshot.tenant_client_id == tenant_client_id,
            AnalyticsSnapshot.snapshot_date >= start_date,
            AnalyticsSnapshot.snapshot_date <= end_date,
        )

        if snapshot_types:
            query = query.where(AnalyticsSnapshot.snapshot_type.in_(snapshot_types))

        query = query.order_by(
            AnalyticsSnapshot.snapshot_date.desc(), AnalyticsSnapshot.snapshot_type
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def filter_snapshots(
        self, filters: AnalyticsSnapshotFilter
    ) -> Sequence[AnalyticsSnapshot]:
        """Filter snapshots based on provided criteria"""
        query = select(AnalyticsSnapshot)

        if filters.tenant_client_id:
            query = query.where(
                AnalyticsSnapshot.tenant_client_id == filters.tenant_client_id
            )

        if filters.snapshot_type:
            query = query.where(
                AnalyticsSnapshot.snapshot_type == filters.snapshot_type
            )

        if filters.snapshot_date:
            query = query.where(
                AnalyticsSnapshot.snapshot_date >= filters.snapshot_date
            )

        if filters.snapshot_date_to:
            query = query.where(
                AnalyticsSnapshot.snapshot_date <= filters.snapshot_date_to
            )

        query = query.order_by(
            AnalyticsSnapshot.snapshot_date.desc(), AnalyticsSnapshot.snapshot_type
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def delete_old_snapshots(
        self, tenant_client_id: UUID, keep_days: int = 365
    ) -> int:
        """Delete snapshots older than specified days"""
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=keep_days)

        # Find count first
        count_query = select(func.count()).where(
            AnalyticsSnapshot.tenant_client_id == tenant_client_id,
            AnalyticsSnapshot.snapshot_date < cutoff_date,
        )
        result = await self.session.execute(count_query)
        count = result.scalar() or 0

        if count > 0:
            # Execute delete
            from sqlalchemy import delete
            stmt = delete(AnalyticsSnapshot).where(
                AnalyticsSnapshot.tenant_client_id == tenant_client_id,
                AnalyticsSnapshot.snapshot_date < cutoff_date,
            )
            await self.session.execute(stmt)
            await self.session.commit()

        return count

    async def get_snapshot_summary(self, tenant_client_id: UUID) -> dict:
        """Get summary statistics for snapshots"""
        query = select(
            func.count(AnalyticsSnapshot.id).label("total_snapshots"),
            func.count(func.distinct(AnalyticsSnapshot.snapshot_type)).label(
                "snapshot_types"
            ),
            func.min(AnalyticsSnapshot.snapshot_date).label("earliest_date"),
            func.max(AnalyticsSnapshot.snapshot_date).label("latest_date"),
        ).where(AnalyticsSnapshot.tenant_client_id == tenant_client_id)

        result = await self.session.execute(query)
        row = result.one()

        return {
            "total_snapshots": row.total_snapshots,
            "snapshot_types": row.snapshot_types,
            "earliest_date": row.earliest_date,
            "latest_date": row.latest_date,
        }

    async def get_snapshot_by_hash(self, data_hash: str) -> Optional[AnalyticsSnapshot]:
        """Get snapshot by data hash"""
        query = select(AnalyticsSnapshot).where(
            AnalyticsSnapshot.data_hash == data_hash
        )
        result = await self.session.execute(query.limit(1))
        return result.scalar_one_or_none()

    async def get_trend_data(
        self,
        tenant_client_id: UUID,
        snapshot_type: SnapshotType,
        metric_path: str,
        start_date: datetime,
        end_date: datetime,
    ) -> list[dict]:
        """Get trend data for a specific metric from snapshots"""
        query = (
            select(
                AnalyticsSnapshot.snapshot_date,
                AnalyticsSnapshot.snapshot_data[metric_path].label("metric_value"),
            )
            .where(
                AnalyticsSnapshot.tenant_client_id == tenant_client_id,
                AnalyticsSnapshot.snapshot_type == snapshot_type,
                AnalyticsSnapshot.snapshot_date >= start_date,
                AnalyticsSnapshot.snapshot_date <= end_date,
                AnalyticsSnapshot.snapshot_data.has_key(metric_path),  # type: ignore
            )
            .order_by(AnalyticsSnapshot.snapshot_date.asc())
        )

        result = await self.session.execute(query)
        rows = result.all()

        return [{"date": row.snapshot_date, "value": row.metric_value} for row in rows]
