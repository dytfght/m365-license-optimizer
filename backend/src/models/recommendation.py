"""
Recommendation models for license optimization
Stores individual user-level license recommendations
"""
from decimal import Decimal
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Optional
from uuid import UUID as UUID_TYPE

if TYPE_CHECKING:
    from .analysis import Analysis
    from .user import User

from sqlalchemy import DECIMAL, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class RecommendationStatus(str, PyEnum):
    """Status of a recommendation"""

    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class Recommendation(Base, UUIDMixin, TimestampMixin):
    """
    Represents a license optimization recommendation for a specific user.
    Generated during analysis runs.
    """

    __tablename__ = "recommendations"
    __table_args__ = {"schema": "optimizer"}

    # Foreign key to analysis
    analysis_id: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("optimizer.analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Foreign key to user
    user_id: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("optimizer.users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # License information
    current_sku: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Current SKU ID (null if no license)"
    )

    recommended_sku: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Recommended SKU ID (null = remove license)"
    )

    # Financial impact
    savings_monthly: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Monthly savings (can be negative for upgrades)",
    )

    # Explanation
    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Explanation for recommendation (e.g., 'Inactive user >90 days')",
    )

    # Recommendation status
    status: Mapped[RecommendationStatus] = mapped_column(
        Enum(RecommendationStatus, name="recommendation_status", schema="optimizer"),
        default=RecommendationStatus.PENDING,
        nullable=False,
        index=True,
    )

    # Relationships
    analysis: Mapped["Analysis"] = relationship(
        "Analysis", back_populates="recommendations"
    )
    user: Mapped["User"] = relationship("User", back_populates="recommendations")

    def __repr__(self) -> str:
        return (
            f"<Recommendation(id={self.id}, user_id={self.user_id}, "
            f"current={self.current_sku}, recommended={self.recommended_sku}, "
            f"savings=${self.savings_monthly})>"
        )
