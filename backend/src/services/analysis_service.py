"""
Analysis Service - Core logic for license optimization
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.analysis import Analysis, AnalysisStatus
from ..models.usage_metrics import UsageMetrics
from ..models.user import User
from ..repositories.analysis_repository import AnalysisRepository
from ..repositories.product_repository import ProductRepository
from ..repositories.recommendation_repository import RecommendationRepository
from ..repositories.usage_metrics_repository import UsageMetricsRepository
from ..repositories.user_repository import UserRepository

logger = structlog.get_logger(__name__)

# SKU mapping for common Microsoft 365 licenses
# Maps SKU to required services
SKU_TO_SERVICES = {
    # Microsoft 365 E5
    "06ebc4ee-1bb5-47dd-8120-11324bc54e06": [
        "Exchange",
        "OneDrive",
        "SharePoint",
        "Teams",
        "Office",
        "Advanced",
    ],
    # Microsoft 365 E3
    "05e9a617-0261-4cee-bb44-138d3ef5d965": [
        "Exchange",
        "OneDrive",
        "SharePoint",
        "Teams",
        "Office",
    ],
    # Microsoft 365 E1
    "18181a46-0d4e-45cd-891e-60aabd171b4e": [
        "Exchange",
        "OneDrive",
        "SharePoint",
        "Teams",
    ],
    # Microsoft 365 F3
    "66b55226-6b4f-492c-910c-a3b7a3c9d993": ["Exchange", "OneDrive", "Teams"],
    # Office 365 E5
    "c7df2760-2c81-4ef7-b578-5b5392b571df": [
        "Exchange",
        "OneDrive",
        "SharePoint",
        "Teams",
        "Office",
        "Advanced",
    ],
    # Office 365 E3
    "6fd2c87f-b296-42f0-b197-1e91e994b900": [
        "Exchange",
        "OneDrive",
        "SharePoint",
        "Teams",
        "Office",
    ],
    # Exchange Online Plan 1
    "4b9405b0-7788-4568-add1-99614e613b69": ["Exchange"],
    # Exchange Online Plan 2
    "19ec0d23-8335-4cbd-94ac-6050e30712fa": ["Exchange"],
}

# SKU names for reference (used in reason field)
SKU_NAMES = {
    "06ebc4ee-1bb5-47dd-8120-11324bc54e06": "Microsoft 365 E5",
    "05e9a617-0261-4cee-bb44-138d3ef5d965": "Microsoft 365 E3",
    "18181a46-0d4e-45cd-891e-60aabd171b4e": "Microsoft 365 E1",
    "66b55226-6b4f-492c-910c-a3b7a3c9d993": "Microsoft 365 F3",
    "c7df2760-2c81-4ef7-b578-5b5392b571df": "Office 365 E5",
    "6fd2c87f-b296-42f0-b197-1e91e994b900": "Office 365 E3",
    "4b9405b0-7788-4568-add1-99614e613b69": "Exchange Online Plan 1",
    "19ec0d23-8335-4cbd-94ac-6050e30712fa": "Exchange Online Plan 2",
}


class AnalysisService:
    """Service for running license optimization analyses"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.analysis_repo = AnalysisRepository(session)
        self.recommendation_repo = RecommendationRepository(session)
        self.user_repo = UserRepository(session)
        self.usage_repo = UsageMetricsRepository(session)
        self.product_repo = ProductRepository(session)

    async def run_analysis(self, tenant_id: UUID) -> Analysis:
        """
        Run complete license optimization analysis for a tenant.

        Args:
            tenant_id: Tenant UUID

        Returns:
            Analysis entity with results
        """
        logger.info("analysis_started", tenant_id=tenant_id)

        try:
            # Create analysis record
            analysis = await self.analysis_repo.create_analysis(
                tenant_id=tenant_id,
                summary={},
                analysis_date=datetime.utcnow(),
            )

            # Fetch all data
            users = await self.user_repo.get_by_tenant(tenant_id, limit=10000)

            if not users:
                # No users to analyze
                summary = {
                    "total_users": 0,
                    "total_current_cost": 0.0,
                    "total_optimized_cost": 0.0,
                    "potential_savings_monthly": 0.0,
                    "potential_savings_annual": 0.0,
                    "recommendations_count": 0,
                    "breakdown": {
                        "remove": 0,
                        "downgrade": 0,
                        "upgrade": 0,
                        "no_change": 0,
                    },
                }
                await self.analysis_repo.update_status(
                    UUID(str(analysis.id)), AnalysisStatus.COMPLETED, summary=summary
                )
                return analysis

            # Fetch usage metrics for the last 28 days
            cutoff_date = datetime.utcnow().date() - timedelta(days=28)

            # Calculate current costs and generate recommendations
            recommendations_data = []
            total_current_cost = Decimal("0.00")
            total_optimized_cost = Decimal("0.00")
            breakdown = {"remove": 0, "downgrade": 0, "upgrade": 0, "no_change": 0}

            for user in users:
                # Get user's usage data
                usage_metrics = await self.usage_repo.get_by_user_and_period(
                    user_id=UUID(str(user.id)),
                    period="D28",
                    start_date=cutoff_date,
                    end_date=datetime.utcnow().date(),
                )

                # Calculate usage scores
                usage_scores = self._calculate_usage_scores(usage_metrics)

                # Get current licenses
                current_sku = None
                if user.license_assignments:
                    # Take first license (simplified)
                    current_sku = user.license_assignments[0].sku_id

                # Get current cost (simplified - assume $10/user/month if licensed)
                current_cost = Decimal("10.00") if current_sku else Decimal("0.00")
                total_current_cost += current_cost

                # Generate recommendation
                recommendation = await self._generate_recommendation(
                    user=user,
                    usage_scores=usage_scores,
                    current_sku=current_sku,
                    current_cost=current_cost,
                )

                if recommendation:
                    recommendations_data.append(
                        {
                            "analysis_id": analysis.id,
                            "user_id": user.id,
                            "current_sku": recommendation["current_sku"],
                            "recommended_sku": recommendation["recommended_sku"],
                            "savings_monthly": recommendation["savings_monthly"],
                            "reason": recommendation["reason"],
                        }
                    )
                    total_optimized_cost += (
                        current_cost - recommendation["savings_monthly"]
                    )

                    # Update breakdown
                    if recommendation["type"] == "remove":
                        breakdown["remove"] += 1
                    elif recommendation["type"] == "downgrade":
                        breakdown["downgrade"] += 1
                    elif recommendation["type"] == "upgrade":
                        breakdown["upgrade"] += 1
                else:
                    breakdown["no_change"] += 1
                    total_optimized_cost += current_cost

            # Bulk insert recommendations
            if recommendations_data:
                await self.recommendation_repo.bulk_insert_recommendations(
                    recommendations_data
                )

            # Calculate savings
            potential_savings_monthly = float(total_current_cost - total_optimized_cost)
            potential_savings_annual = potential_savings_monthly * 12

            # Build summary
            summary = {
                "total_users": len(users),
                "total_current_cost": float(total_current_cost),
                "total_optimized_cost": float(total_optimized_cost),
                "potential_savings_monthly": potential_savings_monthly,
                "potential_savings_annual": potential_savings_annual,
                "recommendations_count": len(recommendations_data),
                "breakdown": breakdown,
            }

            # Update analysis status to completed
            await self.analysis_repo.update_status(
                UUID(str(analysis.id)), AnalysisStatus.COMPLETED, summary=summary
            )

            await self.session.commit()

            logger.info(
                "analysis_completed",
                analysis_id=analysis.id,
                tenant_id=tenant_id,
                savings_monthly=potential_savings_monthly,
                recommendations=len(recommendations_data),
            )

            return analysis

        except Exception as e:
            logger.error(
                "analysis_failed", tenant_id=tenant_id, error=str(e), exc_info=True
            )
            # Mark analysis as failed
            await self.analysis_repo.update_status(
                UUID(str(analysis.id)),
                AnalysisStatus.FAILED,
                error_message=str(e),
            )
            await self.session.commit()
            raise

    def _calculate_usage_scores(
        self, usage_metrics: list[UsageMetrics]
    ) -> dict[str, float]:
        """
        Calculate usage scores per service based on metrics.

        Args:
            usage_metrics: List of UsageMetrics for user

        Returns:
            Dict mapping service name to usage score (0.0 to 1.0)
        """
        if not usage_metrics:
            return {
                "Exchange": 0.0,
                "OneDrive": 0.0,
                "SharePoint": 0.0,
                "Teams": 0.0,
                "Office": 0.0,
            }

        # Take most recent metrics
        latest_metrics = usage_metrics[0]

        scores = {}

        # Email score (based on email activity)
        email_activity = latest_metrics.email_activity or {}
        send_count = email_activity.get("send_count", 0)
        receive_count = email_activity.get("receive_count", 0)
        scores["Exchange"] = min(1.0, (send_count + receive_count) / 100.0)

        # OneDrive score (based on file activity)
        onedrive_activity = latest_metrics.onedrive_activity or {}
        file_count = onedrive_activity.get("viewed_or_edited_file_count", 0)
        scores["OneDrive"] = min(1.0, file_count / 50.0)

        # SharePoint score
        sharepoint_activity = latest_metrics.sharepoint_activity or {}
        sp_file_count = sharepoint_activity.get("viewed_or_edited_file_count", 0)
        scores["SharePoint"] = min(1.0, sp_file_count / 50.0)

        # Teams score (based on messages and meetings)
        teams_activity = latest_metrics.teams_activity or {}
        messages = teams_activity.get("team_chat_message_count", 0)
        meetings = teams_activity.get("meeting_count", 0)
        scores["Teams"] = min(1.0, (messages + meetings * 10) / 100.0)

        # Office score (based on web/desktop activation)
        office_activity = latest_metrics.office_web_activity or {}
        office_count = office_activity.get("viewed_or_edited_file_count", 0)
        scores["Office"] = (
            min(1.0, office_count / 30.0)
            if office_count > 0
            else (1.0 if latest_metrics.office_desktop_activated else 0.0)
        )

        return scores

    async def _generate_recommendation(
        self,
        user: User,
        usage_scores: dict[str, float],
        current_sku: str | None,
        current_cost: Decimal,
    ) -> dict[str, Any] | None:
        """
        Generate a recommendation for a user based on usage.

        Args:
            user: User entity
            usage_scores: Usage scores by service
            current_sku: Current SKU ID
            current_cost: Current monthly cost

        Returns:
            Recommendation dict or None if no recommendation
        """
        # If no current license, no recommendation
        if not current_sku:
            return None

        # Check if user is inactive (not enabled or very low usage)
        if not user.account_enabled:
            return {
                "type": "remove",
                "current_sku": current_sku,
                "recommended_sku": None,
                "savings_monthly": current_cost,
                "reason": "User account is disabled. Recommended to remove license.",
            }

        # Check if all services have very low usage (<0.05 threshold)
        max_usage = max(usage_scores.values())
        if max_usage < 0.05:
            return {
                "type": "remove",
                "current_sku": current_sku,
                "recommended_sku": None,
                "savings_monthly": current_cost,
                "reason": "User inactive for >90 days (no significant activity detected). Recommended to remove license.",
            }

        # Determine required services based on usage (threshold 0.1)
        required_services = [
            service for service, score in usage_scores.items() if score >= 0.1
        ]

        if not required_services:
            # No services used above threshold
            return {
                "type": "remove",
                "current_sku": current_sku,
                "recommended_sku": None,
                "savings_monthly": current_cost,
                "reason": "Very low usage across all services. Recommended to remove license.",
            }

        # Find optimal SKU
        current_sku_name = SKU_NAMES.get(current_sku, f"SKU {current_sku}")

        # Check for downgrade opportunities
        # E5 → E3 if no Advanced services used
        if (
            "Advanced" in SKU_TO_SERVICES.get(current_sku, [])
            and "Advanced" not in required_services
        ):
            # Recommend E3
            e3_sku = "05e9a617-0261-4cee-bb44-138d3ef5d965"
            savings = current_cost * Decimal("0.3")  # Assume 30% savings
            return {
                "type": "downgrade",
                "current_sku": current_sku,
                "recommended_sku": e3_sku,
                "savings_monthly": savings,
                "reason": f"Low usage of advanced features. Downgrade from {current_sku_name} to Microsoft 365 E3 to save costs.",
            }

        # E3 → E1 if only basic services used (Exchange, OneDrive, SharePoint, Teams)
        if current_sku in [
            "05e9a617-0261-4cee-bb44-138d3ef5d965",
            "6fd2c87f-b296-42f0-b197-1e91e994b900",
        ]:
            if "Office" not in required_services:
                e1_sku = "18181a46-0d4e-45cd-891e-60aabd171b4e"
                savings = current_cost * Decimal("0.4")  # Assume 40% savings
                return {
                    "type": "downgrade",
                    "current_sku": current_sku,
                    "recommended_sku": e1_sku,
                    "savings_monthly": savings,
                    "reason": f"No Office desktop usage detected. Downgrade from {current_sku_name} to Microsoft 365 E1 to save costs.",
                }

        # E1/E3 → F3 if only Exchange, OneDrive, Teams (no SharePoint)
        if current_sku in [
            "18181a46-0d4e-45cd-891e-60aabd171b4e",
            "05e9a617-0261-4cee-bb44-138d3ef5d965",
        ]:
            if (
                "SharePoint" not in required_services
                and "Office" not in required_services
            ):
                f3_sku = "66b55226-6b4f-492c-910c-a3b7a3c9d993"
                savings = current_cost * Decimal("0.5")  # Assume 50% savings
                return {
                    "type": "downgrade",
                    "current_sku": current_sku,
                    "recommended_sku": f3_sku,
                    "savings_monthly": savings,
                    "reason": f"Minimal collaboration usage. Downgrade from {current_sku_name} to Microsoft 365 F3 for frontline workers.",
                }

        # No recommendation if usage matches current SKU
        return None

    async def get_analysis_summary(self, analysis_id: UUID) -> dict[str, Any]:
        """
        Get detailed summary for an analysis.

        Args:
            analysis_id: Analysis UUID

        Returns:
            Summary dict
        """
        analysis = await self.analysis_repo.get_by_id(analysis_id)
        if not analysis:
            raise ValueError(f"Analysis {analysis_id} not found")

        return analysis.summary
