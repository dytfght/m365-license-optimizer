"""
Analysis models for license optimization
Stores analysis runs and their results
"""
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Optional
from uuid import UUID as UUID_TYPE

if TYPE_CHECKING:
    from .recommendation import Recommendation
    from .tenant import TenantClient

from sqlalchemy import DateTime, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class AnalysisStatus(str, PyEnum):
    """Status of an analysis run"""

    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Analysis(Base, UUIDMixin, TimestampMixin):
    """
    Represents a license optimization analysis run.
    Stores summary of cost analysis and potential savings.
    """

    __tablename__ = "analyses"
    __table_args__ = {"schema": "optimizer"}

    # Foreign key to tenant
    tenant_client_id: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("optimizer.tenant_clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Analysis metadata
    analysis_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Date and time when analysis was run",
    )

    status: Mapped[AnalysisStatus] = mapped_column(
        Enum(AnalysisStatus, name="analysis_status", schema="optimizer"),
        default=AnalysisStatus.PENDING,
        nullable=False,
        index=True,
    )

    # Analysis results (JSONB for flexibility)
    summary: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
        comment="Analysis summary with totals, costs, savings, and breakdown",
    )

    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Error message if status is FAILED"
    )

    # Relationships
    tenant: Mapped["TenantClient"] = relationship(
        "TenantClient", back_populates="analyses"
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(
        "Recommendation",
        back_populates="analysis",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<Analysis(id={self.id}, tenant_id={self.tenant_client_id}, "
            f"status={self.status}, date={self.analysis_date})>"
        )
