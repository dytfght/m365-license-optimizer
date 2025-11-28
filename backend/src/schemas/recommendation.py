"""
Pydantic schemas for Recommendation models
"""
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class RecommendationBase(BaseModel):
    """Base recommendation schema with common fields"""

    analysis_id: UUID = Field(..., description="Analysis UUID")
    user_id: UUID = Field(..., description="User UUID")
    current_sku: str | None = Field(
        None, description="Current SKU ID (null if no license)"
    )
    recommended_sku: str | None = Field(
        None, description="Recommended SKU ID (null = remove license)"
    )
    savings_monthly: Decimal = Field(
        ..., description="Monthly savings (can be negative for upgrades)"
    )
    reason: str = Field(..., description="Explanation for recommendation")


class RecommendationCreate(RecommendationBase):
    """Schema for creating a new recommendation"""

    pass


class RecommendationResponse(RecommendationBase):
    """Response schema for recommendation data"""

    id: UUID = Field(..., description="Recommendation UUID")
    status: str = Field(
        ..., description="Recommendation status (pending/accepted/rejected)"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")

    class Config:
        from_attributes = True


class ApplyRecommendationRequest(BaseModel):
    """Request schema for applying/rejecting a recommendation"""

    action: str = Field(
        ...,
        description="Action to take: 'accept' or 'reject'",
        pattern="^(accept|reject)$",
    )


class ApplyRecommendationResponse(BaseModel):
    """Response schema for apply/reject action"""

    recommendation_id: UUID = Field(..., description="Recommendation UUID")
    status: str = Field(..., description="New status (accepted/rejected)")
    message: str = Field(..., description="Success message")


class RecommendationList(BaseModel):
    """Response schema for list of recommendations"""

    recommendations: list[RecommendationResponse] = Field(
        ..., description="List of recommendations"
    )
    total: int = Field(..., description="Total number of recommendations")
