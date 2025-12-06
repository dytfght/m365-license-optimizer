"""
Repository for Analysis operations
"""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.analysis import Analysis, AnalysisStatus
from .base import BaseRepository

logger = structlog.get_logger(__name__)


class AnalysisRepository(BaseRepository[Analysis]):
    """Repository for Analysis CRUD operations"""

    def __init__(self, session: AsyncSession):
        super().__init__(Analysis, session)

    async def create_analysis(
        self, tenant_id: UUID, summary: dict, analysis_date: Optional[datetime] = None
    ) -> Analysis:
        """
        Create a new analysis for a tenant.

        Args:
            tenant_id: Tenant UUID
            summary: Analysis summary dict
            analysis_date: Date of analysis (defaults to now)

        Returns:
            Analysis entity
        """
        if analysis_date is None:
            analysis_date = datetime.now(timezone.utc)

        analysis = Analysis(
            tenant_client_id=tenant_id,
            analysis_date=analysis_date,
            status=AnalysisStatus.PENDING,
            summary=summary,
        )

        self.session.add(analysis)
        await self.session.flush()
        await self.session.refresh(analysis)

        logger.info(
            "analysis_created",
            analysis_id=analysis.id,
            tenant_id=tenant_id,
            status=analysis.status,
        )

        return analysis

    async def get_by_id_with_recommendations(
        self, analysis_id: UUID
    ) -> Analysis | None:
        """
        Get analysis by ID with recommendations preloaded.

        Args:
            analysis_id: Analysis UUID

        Returns:
            Analysis entity with recommendations, or None
        """
        result = await self.session.execute(
            select(Analysis)
            .where(Analysis.id == analysis_id)
            .options(selectinload(Analysis.recommendations))
        )
        return result.scalar_one_or_none()

    async def get_by_tenant(
        self, tenant_id: UUID, limit: int = 100, offset: int = 0
    ) -> list[Analysis]:
        """
        Get all analyses for a tenant with pagination.

        Args:
            tenant_id: Tenant UUID
            limit: Max number of results
            offset: Offset for pagination

        Returns:
            List of Analysis entities
        """
        result = await self.session.execute(
            select(Analysis)
            .where(Analysis.tenant_client_id == tenant_id)
            .order_by(Analysis.analysis_date.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        analysis_id: UUID,
        status: AnalysisStatus,
        summary: Optional[dict] = None,
        error_message: Optional[str] = None,
    ) -> Analysis:
        """
        Update analysis status and optionally summary/error.

        Args:
            analysis_id: Analysis UUID
            status: New status
            summary: Updated summary dict (optional)
            error_message: Error message if FAILED (optional)

        Returns:
            Updated Analysis entity

        Raises:
            ValueError: If analysis not found
        """
        analysis = await self.get_by_id(analysis_id)
        if not analysis:
            raise ValueError(f"Analysis {analysis_id} not found")

        analysis.status = status
        if summary is not None:
            analysis.summary = summary
        if error_message is not None:
            analysis.error_message = error_message

        await self.session.flush()
        await self.session.refresh(analysis)

        logger.info(
            "analysis_status_updated",
            analysis_id=analysis_id,
            new_status=status.value,
        )

        return analysis

    async def count_by_tenant(self, tenant_id: UUID) -> int:
        """
        Count analyses for a tenant.

        Args:
            tenant_id: Tenant UUID

        Returns:
            Count of analyses
        """
        from sqlalchemy import func

        result = await self.session.execute(
            select(func.count(Analysis.id)).where(
                Analysis.tenant_client_id == tenant_id
            )
        )
        return result.scalar_one()
