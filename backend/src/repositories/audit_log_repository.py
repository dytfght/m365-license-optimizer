"""
Audit Log Repository for LOT 10
Handles database operations for audit logs.
"""
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.audit_log import AuditLog


class AuditLogRepository:
    """Repository for AuditLog database operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize repository.

        Args:
            db: Async database session
        """
        self.db = db

    async def create(self, log_data: dict) -> AuditLog:
        """
        Create a new audit log entry.

        Args:
            log_data: Dictionary with log fields

        Returns:
            Created AuditLog
        """
        log_entry = AuditLog(**log_data)
        self.db.add(log_entry)
        await self.db.flush()
        return log_entry

    async def get_by_id(self, log_id: UUID) -> Optional[AuditLog]:
        """
        Get a log entry by ID.

        Args:
            log_id: Log UUID

        Returns:
            AuditLog or None
        """
        result = await self.db.execute(
            select(AuditLog).where(AuditLog.id == log_id)
        )
        return result.scalar_one_or_none()

    async def get_by_request_id(self, request_id: str) -> list[AuditLog]:
        """
        Get all log entries for a request.

        Args:
            request_id: Request UUID string

        Returns:
            List of AuditLog entries
        """
        result = await self.db.execute(
            select(AuditLog)
            .where(AuditLog.request_id == request_id)
            .order_by(AuditLog.created_at)
        )
        return list(result.scalars().all())

    async def list_by_tenant(
        self,
        tenant_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[AuditLog], int]:
        """
        List logs for a specific tenant.

        Args:
            tenant_id: Tenant UUID
            limit: Maximum results
            offset: Skip count

        Returns:
            Tuple of (logs, total count)
        """
        # Count query
        count_result = await self.db.execute(
            select(func.count(AuditLog.id))
            .where(AuditLog.tenant_id == tenant_id)
        )
        total = count_result.scalar() or 0

        # Data query
        result = await self.db.execute(
            select(AuditLog)
            .where(AuditLog.tenant_id == tenant_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        logs = list(result.scalars().all())

        return logs, total

    async def list_by_user(
        self,
        user_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[AuditLog], int]:
        """
        List logs for a specific user.

        Args:
            user_id: User UUID
            limit: Maximum results
            offset: Skip count

        Returns:
            Tuple of (logs, total count)
        """
        count_result = await self.db.execute(
            select(func.count(AuditLog.id))
            .where(AuditLog.user_id == user_id)
        )
        total = count_result.scalar() or 0

        result = await self.db.execute(
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        logs = list(result.scalars().all())

        return logs, total

    async def delete_before(self, cutoff_date: datetime) -> int:
        """
        Delete logs before a cutoff date.

        Args:
            cutoff_date: Delete logs created before this date

        Returns:
            Number of deleted logs
        """
        # Count first
        count_result = await self.db.execute(
            select(func.count(AuditLog.id))
            .where(AuditLog.created_at < cutoff_date)
        )
        count = count_result.scalar() or 0

        if count > 0:
            await self.db.execute(
                delete(AuditLog).where(AuditLog.created_at < cutoff_date)
            )

        return count

    async def count_by_level(self, level: str, days: int = 1) -> int:
        """
        Count logs of a specific level in the last N days.

        Args:
            level: Log level to count
            days: Number of days to look back

        Returns:
            Count of logs
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        result = await self.db.execute(
            select(func.count(AuditLog.id))
            .where(AuditLog.level == level.lower())
            .where(AuditLog.created_at >= start_date)
        )
        return result.scalar() or 0
