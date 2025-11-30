"""
Analytics models for storing KPIs and historical snapshots
"""
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Optional
from uuid import UUID as UUID_TYPE

if TYPE_CHECKING:
    from .tenant import TenantClient

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class MetricType(str, PyEnum):
    """Types of analytics metrics"""

    # License optimization metrics
    LICENSE_UTILIZATION = "license_utilization"
    LICENSE_COST = "license_cost"
    LICENSE_SAVINGS = "license_savings"
    LICENSE_EFFICIENCY = "license_efficiency"

    # User activity metrics
    ACTIVE_USERS = "active_users"
    INACTIVE_USERS = "inactive_users"
    DISABLED_USERS = "disabled_users"
    GUEST_USERS = "guest_users"

    # Service usage metrics
    EXCHANGE_USAGE = "exchange_usage"
    SHAREPOINT_USAGE = "sharepoint_usage"
    TEAMS_USAGE = "teams_usage"
    ONEDRIVE_USAGE = "onedrive_usage"

    # Security metrics
    MFA_COVERAGE = "mfa_coverage"
    RISK_SCORE = "risk_score"
    COMPLIANCE_SCORE = "compliance_score"

    @staticmethod
    def _generate_next_value_(
        name: str, start: int, count: int, last_values: list
    ) -> str:
        return name.lower()


class SnapshotType(str, PyEnum):
    """Types of analytics snapshots"""

    LICENSE_INVENTORY = "license_inventory"
    USER_INVENTORY = "user_inventory"
    SERVICE_USAGE = "service_usage"
    SECURITY_STATUS = "security_status"
    COST_ANALYSIS = "cost_analysis"
    OPTIMIZATION_RECOMMENDATIONS = "optimization_recommendations"

    @staticmethod
    def _generate_next_value_(
        name: str, start: int, count: int, last_values: list
    ) -> str:
        return name.lower()


class AnalyticsMetric(Base, UUIDMixin, TimestampMixin):
    """
    Stores KPIs and analytics metrics for tenants.
    Used for tracking performance indicators over time.
    """

    __tablename__ = "analytics_metrics"
    __table_args__ = (
        Index("idx_analytics_metrics_tenant_type", "tenant_client_id", "metric_type"),
        Index("idx_analytics_metrics_period", "period_start", "period_end"),
        Index("idx_analytics_metrics_type_period", "metric_type", "period_start"),
        {"schema": "optimizer"},
    )

    # Foreign key to tenant
    tenant_client_id: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("optimizer.tenant_clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Metric identification
    metric_type: Mapped[MetricType] = mapped_column(
        ENUM(
            MetricType,
            name="metric_type",
            schema="optimizer",
            create_type=False,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        index=True,
    )
    metric_name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Human-readable metric name"
    )

    # Metric value (stored as string for flexibility, can represent numbers, percentages, etc.)
    value: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Metric value (can be number, percentage, etc.)",
    )

    # Time period for the metric
    period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Start of the measurement period",
    )
    period_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="End of the measurement period"
    )

    # Optional unit for the metric
    unit: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Unit of measurement (%, users, GB, etc.)"
    )

    # Additional context data
    context: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True, comment="Additional context data for the metric"
    )

    # Relationships
    tenant: Mapped["TenantClient"] = relationship(
        "TenantClient", back_populates="analytics_metrics"
    )

    def __repr__(self) -> str:
        return (
            f"<AnalyticsMetric(id={self.id}, tenant_id={self.tenant_client_id}, "
            f"type={self.metric_type}, name='{self.metric_name}', value={self.value})>"
        )


class AnalyticsSnapshot(Base, UUIDMixin, TimestampMixin):
    """
    Stores historical snapshots of analytics data.
    Used for trend analysis and historical reporting.
    """

    __tablename__ = "analytics_snapshots"
    __table_args__ = (
        Index(
            "idx_analytics_snapshots_tenant_type_date",
            "tenant_client_id",
            "snapshot_type",
            "snapshot_date",
        ),
        Index("idx_analytics_snapshots_type_date", "snapshot_type", "snapshot_date"),
        {"schema": "optimizer"},
    )

    # Foreign key to tenant
    tenant_client_id: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("optimizer.tenant_clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Snapshot identification
    snapshot_type: Mapped[SnapshotType] = mapped_column(
        ENUM(
            SnapshotType,
            name="snapshot_type",
            schema="optimizer",
            create_type=False,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        index=True,
    )

    # Snapshot date (when the data was captured)
    snapshot_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Date when the snapshot was taken",
    )

    # Snapshot data (flexible JSON structure)
    snapshot_data: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
        comment="Snapshot data in JSON format",
    )

    # Optional metadata about the snapshot
    snapshot_metadata: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True, comment="Additional metadata about the snapshot"
    )

    # Optional hash for data integrity
    data_hash: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="SHA-256 hash of the snapshot data for integrity checking",
    )

    # Relationships
    tenant: Mapped["TenantClient"] = relationship(
        "TenantClient", back_populates="analytics_snapshots"
    )

    def __repr__(self) -> str:
        return (
            f"<AnalyticsSnapshot(id={self.id}, tenant_id={self.tenant_client_id}, "
            f"type={self.snapshot_type}, date={self.snapshot_date})>"
        )
