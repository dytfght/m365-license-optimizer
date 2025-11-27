"""
Repository for Recommendation operations
"""
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.recommendation import Recommendation, RecommendationStatus
from .base import BaseRepository

logger = structlog.get_logger(__name__)


class RecommendationRepository(BaseRepository[Recommendation]):
    """Repository for Recommendation CRUD operations"""

    def __init__(self, session: AsyncSession):
        super().__init__(Recommendation, session)

    async def bulk_insert_recommendations(
        self, recommendations: list[dict[str, Any]]
    ) -> list[Recommendation]:
        """
        Bulk insert multiple recommendations.

        Args:
            recommendations: List of dicts with recommendation data

        Returns:
            List of created Recommendation entities
        """
        entities = []
        for rec_data in recommendations:
            rec = Recommendation(**rec_data)
            self.session.add(rec)
            entities.append(rec)

        if entities:
            await self.session.flush()
            # Refresh to load defaults
            for entity in entities:
                await self.session.refresh(entity)

        logger.info(
            "recommendations_bulk_inserted",
            count=len(entities),
        )

        return entities

    async def get_by_analysis(
        self, analysis_id: UUID, limit: int = 1000, offset: int = 0
    ) -> list[Recommendation]:
        """
        Get all recommendations for an analysis.

        Args:
            analysis_id: Analysis UUID
            limit: Max number of results
            offset: Offset for pagination

        Returns:
            List of Recommendation entities
        """
        result = await self.session.execute(
            select(Recommendation)
            .where(Recommendation.analysis_id == analysis_id)
            .order_by(Recommendation.savings_monthly.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_by_user(
        self, user_id: UUID, limit: int = 100, offset: int = 0
    ) -> list[Recommendation]:
        """
        Get all recommendations for a user.

        Args:
            user_id: User UUID
            limit: Max number of results
            offset: Offset for pagination

        Returns:
            List of Recommendation entities
        """
        result = await self.session.execute(
            select(Recommendation)
            .where(Recommendation.user_id == user_id)
            .order_by(Recommendation.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def update_status(
        self, rec_id: UUID, status: RecommendationStatus
    ) -> Recommendation:
        """
        Update recommendation status.

        Args:
            rec_id: Recommendation UUID
            status: New status

        Returns:
            Updated Recommendation entity

        Raises:
            ValueError: If recommendation not found
        """
        recommendation = await self.get_by_id(rec_id)
        if not recommendation:
            raise ValueError(f"Recommendation {rec_id} not found")

        recommendation.status = status
        await self.session.flush()
        await self.session.refresh(recommendation)

        logger.info(
            "recommendation_status_updated",
            recommendation_id=rec_id,
            new_status=status.value,
        )

        return recommendation

    async def count_by_analysis(self, analysis_id: UUID) -> int:
        """
        Count recommendations for an analysis.

        Args:
            analysis_id: Analysis UUID

        Returns:
            Count of recommendations
        """
        from sqlalchemy import func

        result = await self.session.execute(
            select(func.count(Recommendation.id)).where(
                Recommendation.analysis_id == analysis_id
            )
        )
        return result.scalar_one()

    async def get_pending_by_analysis(self, analysis_id: UUID) -> list[Recommendation]:
        """
        Get all pending recommendations for an analysis.

        Args:
            analysis_id: Analysis UUID

        Returns:
            List of pending Recommendation entities
        """
        result = await self.session.execute(
            select(Recommendation)
            .where(
                Recommendation.analysis_id == analysis_id,
                Recommendation.status == RecommendationStatus.PENDING,
            )
            .order_by(Recommendation.savings_monthly.desc())
        )
        return list(result.scalars().all())
