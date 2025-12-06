"""
Pydantic schemas for Analysis models
"""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class AnalysisBase(BaseModel):
    """Base analysis schema with common fields"""

    tenant_client_id: UUID = Field(..., description="Tenant UUID")
    analysis_date: datetime = Field(
        ..., description="Date and time when analysis was run"
    )


class AnalysisCreate(BaseModel):
    """Schema for creating a new analysis"""

    pass  # No input needed, analysis is triggered via tenant_id in route


class AnalysisSummary(BaseModel):
    """Detailed summary structure for analysis results"""

    total_users: int = Field(..., description="Total number of users analyzed")
    total_current_cost: float = Field(..., description="Current monthly cost")
    total_optimized_cost: float = Field(..., description="Optimized monthly cost")
    potential_savings_monthly: float = Field(
        ..., description="Potential monthly savings"
    )
    potential_savings_annual: float = Field(..., description="Potential annual savings")
    recommendations_count: int = Field(
        ..., description="Number of recommendations generated"
    )
    breakdown: dict[str, int] = Field(
        ...,
        description="Breakdown by recommendation type (remove, downgrade, upgrade, no_change)",
    )


class AnalysisResponse(AnalysisBase):
    """Response schema for analysis data"""

    id: UUID = Field(..., description="Analysis UUID")
    status: str = Field(..., description="Analysis status (pending/completed/failed)")
    summary: dict[str, Any] = Field(
        ..., description="Analysis summary with costs and savings"
    )
    error_message: str | None = Field(None, description="Error message if failed")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")

    class Config:
        from_attributes = True


class AnalysisDetailResponse(AnalysisResponse):
    """Detailed analysis response with recommendations included"""

    recommendations: list["RecommendationResponse"] = Field(
        default_factory=list, description="List of recommendations"
    )

    class Config:
        from_attributes = True


class AnalysisList(BaseModel):
    """Response schema for list of analyses"""

    analyses: list[AnalysisResponse] = Field(..., description="List of analyses")
    total: int = Field(..., description="Total number of analyses")


# Import for forward reference
from .recommendation import RecommendationResponse  # noqa: E402

AnalysisDetailResponse.model_rebuild()
