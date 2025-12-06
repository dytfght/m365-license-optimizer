"""
Usage Metrics Repository
Handles CRUD operations for usage metrics from Microsoft Graph reports.
"""
from datetime import date
from typing import Optional
from uuid import UUID

import structlog
from sqlalchemy import and_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.usage_metrics import UsageMetrics
from .base import BaseRepository

logger = structlog.get_logger(__name__)


class UsageMetricsRepository(BaseRepository[UsageMetrics]):
    """Repository for usage metrics operations"""

    def __init__(self, db: AsyncSession):
        super().__init__(UsageMetrics, db)

    async def upsert_usage(
        self,
        user_id: UUID,
        period: str,
        report_date: date,
        last_seen_date: Optional[date] = None,
        email_activity: Optional[dict] = None,
        onedrive_activity: Optional[dict] = None,
        sharepoint_activity: Optional[dict] = None,
        teams_activity: Optional[dict] = None,
        office_web_activity: Optional[dict] = None,
        office_desktop_activated: bool = False,
        storage_used_bytes: int = 0,
        mailbox_size_bytes: int = 0,
    ) -> UsageMetrics:
        """
        Insert or update usage metrics.
        Uses PostgreSQL's ON CONFLICT DO UPDATE (upsert).

        Args:
            user_id: User UUID
            period: Report period (D7, D28, D90, D180)
            report_date: Date of the report
            last_seen_date: Last activity date
            email_activity: Email metrics dict
            onedrive_activity: OneDrive metrics dict
            sharepoint_activity: SharePoint metrics dict
            teams_activity: Teams metrics dict
            office_web_activity: Office web metrics dict
            office_desktop_activated: Whether Office desktop is activated
            storage_used_bytes: OneDrive storage used
            mailbox_size_bytes: Mailbox size

        Returns:
            UsageMetrics instance
        """
        values = {
            "user_id": user_id,
            "period": period,
            "report_date": report_date,
            "last_seen_date": last_seen_date,
            "email_activity": email_activity or {},
            "onedrive_activity": onedrive_activity or {},
            "sharepoint_activity": sharepoint_activity or {},
            "teams_activity": teams_activity or {},
            "office_web_activity": office_web_activity or {},
            "office_desktop_activated": office_desktop_activated,
            "storage_used_bytes": storage_used_bytes,
            "mailbox_size_bytes": mailbox_size_bytes,
        }

        # Use PostgreSQL INSERT ... ON CONFLICT DO UPDATE
        stmt = (
            pg_insert(UsageMetrics)
            .values(**values)
            .on_conflict_do_update(
                constraint="uq_user_period_date",  # UNIQUE constraint name from model
                set_={
                    "last_seen_date": last_seen_date,
                    "email_activity": email_activity or {},
                    "onedrive_activity": onedrive_activity or {},
                    "sharepoint_activity": sharepoint_activity or {},
                    "teams_activity": teams_activity or {},
                    "office_web_activity": office_web_activity or {},
                    "office_desktop_activated": office_desktop_activated,
                    "storage_used_bytes": storage_used_bytes,
                    "mailbox_size_bytes": mailbox_size_bytes,
                },
            )
            .returning(UsageMetrics)
        )

        result = await self.session.execute(stmt)
        usage_metrics = result.scalar_one()
        await self.session.commit()

        logger.debug(
            "usage_metrics_upserted",
            user_id=str(user_id),
            period=period,
            report_date=str(report_date),
        )

        return usage_metrics

    async def get_latest_by_user(
        self, user_id: UUID, period: str = "D28"
    ) -> Optional[UsageMetrics]:
        """
        Get most recent usage metrics for a user.

        Args:
            user_id: User UUID
            period: Report period (default D28)

        Returns:
            UsageMetrics or None
        """
        stmt = (
            select(UsageMetrics)
            .where(
                and_(
                    UsageMetrics.user_id == user_id,
                    UsageMetrics.period == period,
                )
            )
            .order_by(UsageMetrics.report_date.desc())
            .limit(1)
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user_and_period(
        self, user_id: UUID, period: str, start_date: date, end_date: date
    ) -> list[UsageMetrics]:
        """
        Get usage metrics for a user within a date range.

        Args:
            user_id: User UUID
            period: Report period
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            List of UsageMetrics
        """
        stmt = (
            select(UsageMetrics)
            .where(
                and_(
                    UsageMetrics.user_id == user_id,
                    UsageMetrics.period == period,
                    UsageMetrics.report_date >= start_date,
                    UsageMetrics.report_date <= end_date,
                )
            )
            .order_by(UsageMetrics.report_date.desc())
        )

        result = await self.session.execute(stmt)
        metrics = result.scalars().all()

        logger.debug(
            "usage_metrics_fetched_for_period",
            user_id=str(user_id),
            period=period,
            count=len(metrics),
        )

        return list(metrics)

    async def bulk_upsert(self, metrics_data: list[dict]) -> int:
        """
        Bulk upsert multiple usage metrics.
        More efficient for large data sets.

        Args:
            metrics_data: List of dicts with usage metrics fields

        Returns:
            Number of metrics upserted
        """
        if not metrics_data:
            return 0

        # Use PostgreSQL INSERT ... ON CONFLICT DO UPDATE
        stmt = (
            pg_insert(UsageMetrics)
            .values(metrics_data)
            .on_conflict_do_update(
                constraint="uq_user_period_date",
                set_={
                    "last_seen_date": pg_insert(UsageMetrics).excluded.last_seen_date,
                    "email_activity": pg_insert(UsageMetrics).excluded.email_activity,
                    "onedrive_activity": pg_insert(
                        UsageMetrics
                    ).excluded.onedrive_activity,
                    "sharepoint_activity": pg_insert(
                        UsageMetrics
                    ).excluded.sharepoint_activity,
                    "teams_activity": pg_insert(UsageMetrics).excluded.teams_activity,
                    "office_web_activity": pg_insert(
                        UsageMetrics
                    ).excluded.office_web_activity,
                    "office_desktop_activated": pg_insert(
                        UsageMetrics
                    ).excluded.office_desktop_activated,
                    "storage_used_bytes": pg_insert(
                        UsageMetrics
                    ).excluded.storage_used_bytes,
                    "mailbox_size_bytes": pg_insert(
                        UsageMetrics
                    ).excluded.mailbox_size_bytes,
                },
            )
        )

        await self.session.execute(stmt)
        await self.session.commit()

        logger.info("usage_metrics_bulk_upserted", count=len(metrics_data))

        return len(metrics_data)
