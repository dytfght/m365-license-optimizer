"""
Microsoft Product Model
Catalog of Microsoft products and SKUs from Partner Center
"""
from typing import Optional

from sqlalchemy import Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class MicrosoftProduct(Base, UUIDMixin, TimestampMixin):
    """
    Microsoft Product catalog (products + SKUs)

    Stores product information from Partner Center pricing data.
    Separation from prices allows for efficient queries and avoids duplication.
    """

    __tablename__ = "microsoft_products"
    __table_args__ = (
        UniqueConstraint("product_id", "sku_id", name="uq_product_sku"),
        Index("ix_microsoft_products_product_id", "product_id"),
        Index("ix_microsoft_products_sku_id", "sku_id"),
        {"schema": "optimizer"},
    )

    # Product identifiers (from Partner Center)
    product_id: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="Partner Center Product ID"
    )
    sku_id: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="Partner Center SKU ID"
    )

    # Product information
    product_title: Mapped[str] = mapped_column(String(500), nullable=False)
    sku_title: Mapped[str] = mapped_column(String(500), nullable=False)
    publisher: Mapped[str] = mapped_column(
        String(255), nullable=False, server_default="Microsoft Corporation"
    )
    sku_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Additional metadata
    unit_of_measure: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    tags: Mapped[Optional[list]] = mapped_column(
        JSONB, nullable=True, server_default="[]"
    )

    def __repr__(self) -> str:
        return f"<MicrosoftProduct(product_id='{self.product_id}', sku_id='{self.sku_id}', title='{self.sku_title}')>"
