"""
Usage Metrics models
Stores Microsoft 365 usage data from Graph API reports
"""
from datetime import date
from typing import TYPE_CHECKING, Optional
from uuid import UUID as UUID_TYPE

if TYPE_CHECKING:
    from .user import User

from sqlalchemy import BigInteger, Boolean, Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class UsageMetrics(Base, UUIDMixin, TimestampMixin):
    """
    Stores usage metrics from Microsoft Graph reports.
    Includes email, OneDrive, SharePoint, Teams activity.
    """

    __tablename__ = "usage_metrics"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "period", "report_date", name="uq_user_period_date"
        ),
        {"schema": "optimizer"},
    )

    # Foreign key to user
    user_id: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("optimizer.users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Report metadata
    period: Mapped[str] = mapped_column(
        String(10), nullable=False, comment="Period: D7, D28, D90, D180"
    )
    report_date: Mapped[date] = mapped_column(
        Date, nullable=False, index=True, comment="Date of the report"
    )
    last_seen_date: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True, comment="Last activity date"
    )

    # Activity metrics (JSONB for flexibility)
    email_activity: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        default=dict,
        nullable=True,
        comment="Email activity metrics (send_count, receive_count, etc.)",
    )
    onedrive_activity: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        default=dict,
        nullable=True,
        comment="OneDrive activity metrics (viewed, edited, synced, etc.)",
    )
    sharepoint_activity: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        default=dict,
        nullable=True,
        comment="SharePoint activity metrics (viewed, edited, shared, etc.)",
    )
    teams_activity: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        default=dict,
        nullable=True,
        comment="Teams activity metrics (messages, calls, meetings, etc.)",
    )
    office_web_activity: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        default=dict,
        nullable=True,
        comment="Office web activity (Word, Excel, PowerPoint online)",
    )

    # Activation status
    office_desktop_activated: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="Office desktop activated"
    )

    # Storage metrics
    storage_used_bytes: Mapped[int] = mapped_column(
        BigInteger, default=0, nullable=False, comment="OneDrive storage used (bytes)"
    )
    mailbox_size_bytes: Mapped[int] = mapped_column(
        BigInteger, default=0, nullable=False, comment="Mailbox size (bytes)"
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="usage_metrics")

    def __repr__(self) -> str:
        return (
            f"<UsageMetrics(user_id={self.user_id}, period='{self.period}', "
            f"date={self.report_date})>"
        )
