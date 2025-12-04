"""
Audit Log model for LOT 10: Persistent logging in database
Stores all API requests and security events for compliance and debugging.
"""
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional
from uuid import UUID as UUID_TYPE

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class LogLevel(str, PyEnum):
    """Log level enumeration"""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditLog(Base, UUIDMixin, TimestampMixin):
    """
    Persistent audit log for API requests and security events.
    Stored in PostgreSQL for compliance (GDPR Article 30).
    """

    __tablename__ = "audit_logs"
    __table_args__ = {"schema": "optimizer"}

    # Log level and message
    level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Log level: debug, info, warning, error, critical",
    )
    message: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Log message"
    )

    # Request context
    endpoint: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True, comment="API endpoint path"
    )
    method: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True, comment="HTTP method"
    )
    request_id: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True, index=True, comment="Unique request ID"
    )

    # User context (nullable for anonymous requests)
    user_id: Mapped[Optional[UUID_TYPE]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("optimizer.users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="User performing the action",
    )
    tenant_id: Mapped[Optional[UUID_TYPE]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("optimizer.tenant_clients.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Tenant context",
    )

    # Client information
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45), nullable=True, comment="Client IP address (IPv4 or IPv6)"
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="Client user agent"
    )

    # Response information
    response_status: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, index=True, comment="HTTP response status code"
    )
    duration_ms: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Request duration in milliseconds"
    )

    # Additional data (JSON for flexibility)
    extra_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional structured data (headers, params, etc.)",
    )

    # Action category for filtering
    action: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Action category: auth, sync, analysis, gdpr, etc.",
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog(id={self.id}, level='{self.level}', "
            f"endpoint='{self.endpoint}', user_id={self.user_id})>"
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": str(self.id),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "level": self.level,
            "message": self.message,
            "endpoint": self.endpoint,
            "method": self.method,
            "request_id": self.request_id,
            "user_id": str(self.user_id) if self.user_id else None,
            "tenant_id": str(self.tenant_id) if self.tenant_id else None,
            "ip_address": self.ip_address,
            "response_status": self.response_status,
            "duration_ms": self.duration_ms,
            "action": self.action,
            "extra_data": self.extra_data,
        }
