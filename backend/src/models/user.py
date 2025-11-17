"""
User and License models
"""
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

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
    
    # Microsoft Graph ID
    graph_id: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        index=True,
        comment="Microsoft Graph User ID"
    )
    
    # Foreign key to tenant
    tenant_client_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenant_clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Basic user information
    user_principal_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    account_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Extended attributes (from Graph API)
    department: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    job_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    office_location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Group memberships (filtered list)
    member_of_groups: Mapped[Optional[list]] = mapped_column(
        JSONB,
        default=list,
        nullable=True,
        comment="Filtered Azure AD groups (DEPT-*, LIC-*, Executives)"
    )
    
    # Relationships
    tenant: Mapped["TenantClient"] = relationship(
        "TenantClient",
        back_populates="users"
    )
    license_assignments: Mapped[list["LicenseAssignment"]] = relationship(
        "LicenseAssignment",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, upn='{self.user_principal_name}', enabled={self.account_enabled})>"


class LicenseStatus(str, PyEnum):
    """License assignment status"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DISABLED = "disabled"


class AssignmentSource(str, PyEnum):
    """License assignment source"""
    MANUAL = "manual"
    GROUP_BASED = "group_based"
    AUTO = "auto"


class LicenseAssignment(Base, UUIDMixin):
    """
    Represents a license assigned to a user.
    Tracks M365 SKU assignments.
    """
    __tablename__ = "license_assignments"
    __table_args__ = (
        UniqueConstraint('user_id', 'sku_id', name='uq_user_sku'),
    )
    
    # Foreign key to user
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # License information
    sku_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
        comment="Microsoft SKU ID (GUID)"
    )
    
    # Assignment metadata
    assignment_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    status: Mapped[LicenseStatus] = mapped_column(
        Enum(LicenseStatus),
        default=LicenseStatus.ACTIVE,
        nullable=False
    )
    source: Mapped[AssignmentSource] = mapped_column(
        Enum(AssignmentSource),
        default=AssignmentSource.MANUAL,
        nullable=False
    )
    
    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="license_assignments"
    )
    
    def __repr__(self) -> str:
        return f"<LicenseAssignment(user_id={self.user_id}, sku_id='{self.sku_id}', status={self.status})>"
