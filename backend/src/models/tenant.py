"""
Tenant models: TenantClient and TenantAppRegistration
"""
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class OnboardingStatus(str, PyEnum):
    """Tenant onboarding status"""
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"


class TenantClient(Base, UUIDMixin, TimestampMixin):
    """
    Represents a client tenant in the multitenant architecture.
    Each tenant is a separate Microsoft 365 organization.
    """
    __tablename__ = "tenant_clients"
    
    # Basic information
    tenant_id: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        index=True,
        comment="Azure AD Tenant ID"
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
        comment="ISO 3166-1 alpha-2 country code"
    )
    default_language: Mapped[str] = mapped_column(
        String(5),
        default="fr",
        nullable=False,
        comment="Default language (fr or en)"
    )
    
    # Status
    onboarding_status: Mapped[OnboardingStatus] = mapped_column(
        Enum(OnboardingStatus),
        default=OnboardingStatus.PENDING,
        nullable=False
    )
    
    # Partner Center metadata (optional)
    csp_customer_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True,
        comment="Partner Center Customer ID"
    )
    
    # Additional metadata - RENAMED FROM metadata TO metadatas
    metadatas: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional tenant metadata"
    )
    
    # Relationships
    app_registration: Mapped[Optional["TenantAppRegistration"]] = relationship(
        "TenantAppRegistration",
        back_populates="tenant",
        uselist=False,
        cascade="all, delete-orphan"
    )
    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="tenant",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<TenantClient(id={self.id}, name='{self.name}', status={self.onboarding_status})>"


class ConsentStatus(str, PyEnum):
    """App Registration consent status"""
    PENDING = "pending"
    GRANTED = "granted"
    EXPIRED = "expired"
    REVOKED = "revoked"


class TenantAppRegistration(Base, UUIDMixin, TimestampMixin):
    """
    Stores App Registration credentials for each tenant.
    Used for Microsoft Graph API authentication (client credentials flow).
    """
    __tablename__ = "tenant_app_registrations"
    
    # Foreign key to tenant
    tenant_client_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenant_clients.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    
    # App Registration credentials
    client_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        comment="Azure AD Application (client) ID"
    )
    client_secret: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Encrypted client secret (use Fernet)"
    )
    certificate_thumbprint: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="Certificate thumbprint if using certificate auth"
    )
    
    # Configuration
    authority_url: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Azure AD authority URL"
    )
    scopes: Mapped[list[str]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
        comment="List of Microsoft Graph API scopes"
    )
    
    # Consent tracking
    consent_status: Mapped[ConsentStatus] = mapped_column(
        Enum(ConsentStatus),
        default=ConsentStatus.PENDING,
        nullable=False
    )
    consent_granted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Validation
    is_valid: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether credentials have been validated"
    )
    last_validated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Relationships
    tenant: Mapped["TenantClient"] = relationship(
        "TenantClient",
        back_populates="app_registration"
    )
    
    def __repr__(self) -> str:
        return f"<TenantAppRegistration(id={self.id}, client_id='{self.client_id}', status={self.consent_status})>"
