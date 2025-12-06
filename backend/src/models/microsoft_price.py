"""
Microsoft Price Model
Pricing data from Partner Center with temporal validity
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    DECIMAL,
    DateTime,
    Enum,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class MicrosoftPrice(Base, UUIDMixin, TimestampMixin):
    """
    Microsoft pricing with historization and multi-currency support

    Stores pricing information from Partner Center for different:
    - Markets (countries)
    - Currencies
    - Customer segments (Commercial, Education, Charity)
    - Billing plans (Annual, Monthly)
    - Time periods (effective_start_date to effective_end_date)

    This allows tracking price changes over time and supporting
    different pricing tiers for the same product.
    """

    __tablename__ = "microsoft_prices"
    __table_args__ = (
        # Foreign key constraint on composite (product_id, sku_id)
        ForeignKeyConstraint(
            ["product_id", "sku_id"],
            [
                "optimizer.microsoft_products.product_id",
                "optimizer.microsoft_products.sku_id",
            ],
            ondelete="CASCADE",
        ),
        # Unique constraint: one price per variant at a given start date
        UniqueConstraint(
            "product_id",
            "sku_id",
            "market",
            "currency",
            "segment",
            "billing_plan",
            "effective_start_date",
            name="uq_price_variant",
        ),
        Index(
            "ix_microsoft_prices_effective_dates",
            "effective_start_date",
            "effective_end_date",
        ),
        Index("ix_microsoft_prices_product_sku", "product_id", "sku_id"),
        Index("ix_microsoft_prices_market_currency", "market", "currency"),
        {"schema": "optimizer"},
    )

    # Foreign key to product (composite: product_id + sku_id)
    product_id: Mapped[str] = mapped_column(String(50), nullable=False)
    sku_id: Mapped[str] = mapped_column(String(50), nullable=False)

    # Pricing dimensions
    market: Mapped[str] = mapped_column(
        String(5), nullable=False, comment="Market code (ex: AX, FR, US)"
    )
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, comment="ISO 4217 currency code"
    )
    segment: Mapped[str] = mapped_column(
        Enum(
            "Commercial",
            "Education",
            "Charity",
            name="pricing_segment",
            schema="optimizer",
        ),
        nullable=False,
    )

    # Billing details
    term_duration: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="ISO 8601 duration (P1Y=annual, P1M=monthly)",
    )
    billing_plan: Mapped[str] = mapped_column(
        Enum("Annual", "Monthly", name="billing_plan", schema="optimizer"),
        nullable=False,
    )

    # Prices
    unit_price: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    erp_price: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)

    # Validity period (temporal data)
    effective_start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    effective_end_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Metadata
    change_indicator: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="Unchanged"
    )
    pricing_tier_range_min: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    pricing_tier_range_max: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )

    def __repr__(self) -> str:
        return (
            f"<MicrosoftPrice(sku_id='{self.sku_id}', market='{self.market}', "
            f"currency='{self.currency}', unit_price={self.unit_price})>"
        )
