"""
Recommendation Service - Manage recommendations
"""
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.recommendation import Recommendation, RecommendationStatus
from ..repositories.recommendation_repository import RecommendationRepository

logger = structlog.get_logger(__name__)


class RecommendationService:
    """Service for managing license recommendations"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.recommendation_repo = RecommendationRepository(session)

    async def apply_recommendation(self, rec_id: UUID, user_id: UUID) -> Recommendation:
        """
        Mark a recommendation as accepted.

        Args:
            rec_id: Recommendation UUID
            user_id: User UUID (for audit)

        Returns:
            Updated Recommendation entity
        """
        recommendation = await self.recommendation_repo.update_status(
            rec_id, RecommendationStatus.ACCEPTED
        )

        logger.info(
            "recommendation_accepted",
            recommendation_id=rec_id,
            user_id=user_id,
            savings_monthly=float(recommendation.savings_monthly),
        )

        await self.session.commit()

        return recommendation

    async def reject_recommendation(
        self, rec_id: UUID, user_id: UUID
    ) -> Recommendation:
        """
        Mark a recommendation as rejected.

        Args:
            rec_id: Recommendation UUID
            user_id: User UUID (for audit)

        Returns:
            Updated Recommendation entity
        """
        recommendation = await self.recommendation_repo.update_status(
            rec_id, RecommendationStatus.REJECTED
        )

        logger.info(
            "recommendation_rejected",
            recommendation_id=rec_id,
            user_id=user_id,
        )

        await self.session.commit()

        return recommendation

    async def get_user_recommendations(
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
        return await self.recommendation_repo.get_by_user(user_id, limit, offset)

    async def get_analysis_recommendations(
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
        return await self.recommendation_repo.get_by_analysis(
            analysis_id, limit, offset
        )

    async def get_pending_recommendations(
        self, analysis_id: UUID
    ) -> list[Recommendation]:
        """
        Get all pending recommendations for an analysis.

        Args:
            analysis_id: Analysis UUID

        Returns:
            List of pending Recommendation entities
        """
        return await self.recommendation_repo.get_pending_by_analysis(analysis_id)
