"""
Logging Service for LOT 10: Persistent logging in database
Handles storing, querying, and purging audit logs.
"""
from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import UUID

import structlog
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..models.audit_log import AuditLog

logger = structlog.get_logger(__name__)


class LoggingService:
    """
    Service for persistent logging operations.
    Stores logs in PostgreSQL for compliance and debugging.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize logging service.

        Args:
            db: Async database session
        """
        self.db = db

    async def log_to_db(
        self,
        level: str,
        message: str,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        request_id: Optional[str] = None,
        user_id: Optional[UUID] = None,
        tenant_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        response_status: Optional[int] = None,
        duration_ms: Optional[int] = None,
        action: Optional[str] = None,
        extra_data: Optional[dict] = None,
    ) -> AuditLog:
        """
        Store a log entry in the database.

        Args:
            level: Log level (debug, info, warning, error, critical)
            message: Log message
            endpoint: API endpoint path
            method: HTTP method
            request_id: Unique request ID
            user_id: User performing the action
            tenant_id: Tenant context
            ip_address: Client IP address
            user_agent: Client user agent
            response_status: HTTP response status code
            duration_ms: Request duration in milliseconds
            action: Action category (auth, sync, analysis, etc.)
            extra_data: Additional structured data

        Returns:
            Created AuditLog entry
        """
        log_entry = AuditLog(
            level=level.lower(),
            message=message,
            endpoint=endpoint,
            method=method,
            request_id=request_id,
            user_id=user_id,
            tenant_id=tenant_id,
            ip_address=ip_address,
            user_agent=user_agent,
            response_status=response_status,
            duration_ms=duration_ms,
            action=action,
            extra_data=extra_data,
        )

        self.db.add(log_entry)
        await self.db.commit()
        await self.db.refresh(log_entry)

        return log_entry

    async def get_logs(
        self,
        level: Optional[str] = None,
        tenant_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        endpoint: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_status: Optional[int] = None,
        max_status: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[AuditLog], int]:
        """
        Query logs with filters.

        Args:
            level: Filter by log level
            tenant_id: Filter by tenant
            user_id: Filter by user
            endpoint: Filter by endpoint (partial match)
            action: Filter by action category
            start_date: Filter by start date
            end_date: Filter by end date
            min_status: Minimum response status code
            max_status: Maximum response status code
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            Tuple of (logs list, total count)
        """
        query = select(AuditLog)
        count_query = select(func.count(AuditLog.id))

        # Apply filters
        if level:
            query = query.where(AuditLog.level == level.lower())
            count_query = count_query.where(AuditLog.level == level.lower())

        if tenant_id:
            query = query.where(AuditLog.tenant_id == tenant_id)
            count_query = count_query.where(AuditLog.tenant_id == tenant_id)

        if user_id:
            query = query.where(AuditLog.user_id == user_id)
            count_query = count_query.where(AuditLog.user_id == user_id)

        if endpoint:
            query = query.where(AuditLog.endpoint.ilike(f"%{endpoint}%"))
            count_query = count_query.where(AuditLog.endpoint.ilike(f"%{endpoint}%"))

        if action:
            query = query.where(AuditLog.action == action)
            count_query = count_query.where(AuditLog.action == action)

        if start_date:
            query = query.where(AuditLog.created_at >= start_date)
            count_query = count_query.where(AuditLog.created_at >= start_date)

        if end_date:
            query = query.where(AuditLog.created_at <= end_date)
            count_query = count_query.where(AuditLog.created_at <= end_date)

        if min_status:
            query = query.where(AuditLog.response_status >= min_status)
            count_query = count_query.where(AuditLog.response_status >= min_status)

        if max_status:
            query = query.where(AuditLog.response_status <= max_status)
            count_query = count_query.where(AuditLog.response_status <= max_status)

        # Get total count
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar() or 0

        # Apply ordering and pagination
        query = query.order_by(AuditLog.created_at.desc())
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        logs = result.scalars().all()

        return list(logs), total_count

    async def get_log_by_id(self, log_id: UUID) -> Optional[AuditLog]:
        """
        Get a specific log entry by ID.

        Args:
            log_id: Log UUID

        Returns:
            AuditLog or None
        """
        result = await self.db.execute(
            select(AuditLog).where(AuditLog.id == log_id)
        )
        return result.scalar_one_or_none()

    async def purge_old_logs(self, days: Optional[int] = None) -> int:
        """
        Delete logs older than the specified number of days.
        Default is LOG_RETENTION_DAYS from settings (90 days for GDPR).

        Args:
            days: Number of days to retain (default from settings)

        Returns:
            Number of deleted logs
        """
        retention_days = float(days or getattr(settings, "LOG_RETENTION_DAYS", 90) or 90)
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

        # Count logs to be deleted
        count_result = await self.db.execute(
            select(func.count(AuditLog.id)).where(AuditLog.created_at < cutoff_date)
        )
        count = count_result.scalar() or 0

        if count > 0:
            # Delete old logs
            await self.db.execute(
                delete(AuditLog).where(AuditLog.created_at < cutoff_date)
            )
            await self.db.commit()

            logger.info(
                "audit_logs_purged",
                deleted_count=count,
                retention_days=retention_days,
                cutoff_date=cutoff_date.isoformat(),
            )

        return count

    async def get_log_statistics(
        self,
        tenant_id: Optional[UUID] = None,
        days: int = 7,
    ) -> dict[str, Any]:
        """
        Get log statistics for monitoring.

        Args:
            tenant_id: Optional tenant filter
            days: Number of days to analyze

        Returns:
            Statistics dictionary
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        base_query = select(AuditLog).where(AuditLog.created_at >= start_date)
        if tenant_id:
            base_query = base_query.where(AuditLog.tenant_id == tenant_id)

        # Total count
        total_result = await self.db.execute(
            select(func.count(AuditLog.id)).where(AuditLog.created_at >= start_date)
        )
        total = total_result.scalar() or 0

        # Count by level
        levels = {}
        for level in ["debug", "info", "warning", "error", "critical"]:
            level_result = await self.db.execute(
                select(func.count(AuditLog.id))
                .where(AuditLog.created_at >= start_date)
                .where(AuditLog.level == level)
            )
            levels[level] = level_result.scalar() or 0

        # Error rate
        error_count = levels.get("error", 0) + levels.get("critical", 0)
        error_rate = (error_count / total * 100) if total > 0 else 0

        return {
            "period_days": days,
            "total_logs": total,
            "by_level": levels,
            "error_count": error_count,
            "error_rate_percent": round(error_rate, 2),
        }
