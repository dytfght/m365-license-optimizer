"""
User and License models
"""
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Optional
from uuid import UUID as UUID_TYPE

if TYPE_CHECKING:
    from .recommendation import Recommendation
    from .tenant import TenantClient
    from .usage_metrics import UsageMetrics

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class User(Base, UUIDMixin, TimestampMixin):
    """
    Represents a user from Microsoft 365 tenant.
    Synced from Microsoft Graph API.
    """

    __tablename__ = "users"
    __table_args__ = {"schema": "optimizer"}

    # Microsoft Graph ID
    graph_id: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        index=True,
        comment="Microsoft Graph User ID",
    )

    # Foreign key to tenant
    tenant_client_id: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("optimizer.tenant_clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Basic user information
    user_principal_name: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    account_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Authentication (for partner users)
    password_hash: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Hashed password for authentication (partner users only)",
    )

    # Extended attributes (from Graph API)
    department: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    job_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    office_location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Group memberships (filtered list)
    member_of_groups: Mapped[Optional[list]] = mapped_column(
        JSONB,
        default=list,
        nullable=True,
        comment="Filtered Azure AD groups (DEPT-*, LIC-*, Executives)",
    )

    # Relationships
    tenant: Mapped["TenantClient"] = relationship(
        "TenantClient", back_populates="users"
    )
    license_assignments: Mapped[list["LicenseAssignment"]] = relationship(
        "LicenseAssignment", back_populates="user", cascade="all, delete-orphan"
    )
    usage_metrics: Mapped[list["UsageMetrics"]] = relationship(
        "UsageMetrics", back_populates="user", cascade="all, delete-orphan"
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(
        "Recommendation", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, upn='{self.user_principal_name}', enabled={self.account_enabled})>"


class LicenseStatus(str, PyEnum):
    """License assignment status"""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    DISABLED = "disabled"
    TRIAL = "trial"


class AssignmentSource(str, PyEnum):
    """License assignment source"""

    MANUAL = "manual"
    AUTO = "auto"
    GROUP_POLICY = "group_policy"


class LicenseAssignment(Base, UUIDMixin, TimestampMixin):
    """
    Represents a license assigned to a user.
    Tracks M365 SKU assignments.
    """

    __tablename__ = "license_assignments"
    __table_args__ = (
        UniqueConstraint("user_id", "sku_id", name="uq_user_sku"),
        {"schema": "optimizer"},
    )

    # Foreign key to user
    user_id: Mapped[UUID_TYPE] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("optimizer.users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # License information
    sku_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True, comment="Microsoft SKU ID (GUID)"
    )

    # Assignment metadata
    assignment_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[LicenseStatus] = mapped_column(
        Enum(LicenseStatus, name="license_status", schema="optimizer", native_enum=True, values_callable=lambda x: [e.value for e in x]), 
        default=LicenseStatus.ACTIVE, 
        nullable=False
    )
    source: Mapped[AssignmentSource] = mapped_column(
        Enum(AssignmentSource, name="assignment_source", schema="optimizer", native_enum=True, values_callable=lambda x: [e.value for e in x]), 
        default=AssignmentSource.MANUAL, 
        nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="license_assignments")

    def __repr__(self) -> str:
        return f"<LicenseAssignment(user_id={self.user_id}, sku_id='{self.sku_id}', status={self.status})>"
