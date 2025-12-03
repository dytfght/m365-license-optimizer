"""
Report Model - Stores generated PDF and Excel reports
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDMixin


class Report(Base, UUIDMixin):
    """Stores generated reports (PDF or Excel files)"""

    __tablename__ = "reports"
    __table_args__ = {"schema": "optimizer"}

    # Foreign keys
    analysis_id: Mapped[Optional[str]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("optimizer.analyses.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    tenant_client_id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("optimizer.tenant_clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Report metadata
    report_type: Mapped[str] = mapped_column(
        String(10), nullable=False, comment="PDF or EXCEL", index=True
    )
    file_name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Original filename"
    )
    file_path: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="Storage path"
    )
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # Report content metadata
    report_metadata: Mapped[dict] = mapped_column(
        JSONB, default=dict, comment="KPIs, stats, chart data"
    )
    generated_by: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="User email who generated"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="TTL for cleanup", index=True
    )

    # Relations
    analysis = relationship("Analysis", back_populates="reports")
    tenant = relationship("TenantClient", back_populates="reports")

    def __repr__(self) -> str:
        return (
            f"<Report(id={self.id}, type={self.report_type}, "
            f"file={self.file_name}, size={self.file_size_bytes})>"
        )
