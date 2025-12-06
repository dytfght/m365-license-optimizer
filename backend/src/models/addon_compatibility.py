"""
Addon Compatibility Model
Maps add-ons to their compatible base SKUs and manages add-on relationships
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class AddonCompatibility(Base, UUIDMixin, TimestampMixin):
    """
    Addon Compatibility mapping

    Defines relationships between add-ons and their compatible base SKUs,
    including validation rules and metadata for Partner Center integration.
    """

    __tablename__ = "addon_compatibility"
    __table_args__ = (
        Index("ix_addon_compatibility_addon_sku_id", "addon_sku_id"),
        Index("ix_addon_compatibility_base_sku_id", "base_sku_id"),
        Index("ix_addon_compatibility_service_type", "service_type"),
        Index("ix_addon_compatibility_addon_category", "addon_category"),
        Index("ix_addon_compatibility_is_active", "is_active"),
        Index("ix_addon_compatibility_created_at", "created_at"),
        {"schema": "optimizer"},
    )

    # Add-on identification
    addon_sku_id: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="Partner Center SKU ID for the add-on"
    )
    addon_product_id: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="Partner Center Product ID for the add-on"
    )

    # Base SKU compatibility
    base_sku_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Partner Center SKU ID for compatible base SKU",
    )
    base_product_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Partner Center Product ID for compatible base SKU",
    )

    # Service and category information
    service_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Service type (e.g., 'Microsoft 365', 'Dynamics 365')",
    )
    addon_category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Category of add-on (e.g., 'Storage', 'Calling Plan')",
    )

    # Compatibility rules
    min_quantity: Mapped[int] = mapped_column(
        default=1, comment="Minimum quantity required"
    )
    max_quantity: Mapped[Optional[int]] = mapped_column(
        nullable=True, comment="Maximum quantity allowed (null = unlimited)"
    )
    quantity_multiplier: Mapped[int] = mapped_column(
        default=1, comment="Quantity must be multiple of this value"
    )

    # Validation rules
    requires_domain_validation: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="Requires domain-level validation"
    )
    requires_tenant_validation: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="Requires tenant-level validation"
    )
    validation_metadata: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True, comment="Additional validation metadata"
    )

    # Partner Center metadata
    pc_metadata: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True, comment="Partner Center specific metadata"
    )

    # Status and availability
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="Whether this mapping is active"
    )
    effective_date: Mapped[Optional[datetime]] = mapped_column(
        nullable=True, comment="Date when this mapping becomes effective"
    )
    expiration_date: Mapped[Optional[datetime]] = mapped_column(
        nullable=True, comment="Date when this mapping expires"
    )

    # Description and notes
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Description of the compatibility mapping"
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Internal notes about this mapping"
    )

    def __repr__(self) -> str:
        return f"<AddonCompatibility(addon_sku_id='{self.addon_sku_id}', base_sku_id='{self.base_sku_id}', service_type='{self.service_type}')>"

    def is_compatible(self, base_sku_id: str, quantity: int) -> bool:
        """Check if add-on is compatible with given base SKU and quantity"""
        if self.base_sku_id != base_sku_id:
            return False

        if quantity < self.min_quantity:
            return False

        if self.max_quantity is not None and quantity > self.max_quantity:
            return False

        if quantity % self.quantity_multiplier != 0:
            return False

        return True

    def is_available(self) -> bool:
        """Check if this mapping is currently available"""
        if not self.is_active:
            return False

        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)

        if self.effective_date and now < self.effective_date:
            return False

        if self.expiration_date and now > self.expiration_date:
            return False

        return True
