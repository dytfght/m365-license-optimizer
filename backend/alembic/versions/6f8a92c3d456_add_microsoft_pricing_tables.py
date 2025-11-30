"""add_microsoft_pricing_tables

Revision ID: 6f8a92c3d456
Revises: 524ffcf21789
Create Date: 2025-11-25 20:37:00.000000

Adds tables for Microsoft Partner Center pricing data:
- microsoft_products: Product catalog (products + SKUs)
- microsoft_prices: Pricing with temporal validity and multi-market support
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "6f8a92c3d456"
down_revision = "524ffcf21789"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create microsoft_products and microsoft_prices tables"""

    # Note: ENUMs are created automatically by SQLAlchemy when creating tables
    # No need to create them manually here

    # 1. Create microsoft_products table
    op.create_table(
        "microsoft_products",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            sa.String(length=50),
            nullable=False,
            comment="Partner Center Product ID",
        ),
        sa.Column(
            "sku_id",
            sa.String(length=50),
            nullable=False,
            comment="Partner Center SKU ID",
        ),
        sa.Column("product_title", sa.String(length=500), nullable=False),
        sa.Column("sku_title", sa.String(length=500), nullable=False),
        sa.Column(
            "publisher",
            sa.String(length=255),
            nullable=False,
            server_default="Microsoft Corporation",
        ),
        sa.Column("sku_description", sa.Text(), nullable=True),
        sa.Column("unit_of_measure", sa.String(length=50), nullable=True),
        sa.Column(
            "tags",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default="[]",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_id", "sku_id", name="uq_product_sku"),
        schema="optimizer",
    )
    op.create_index(
        "ix_microsoft_products_product_id",
        "microsoft_products",
        ["product_id"],
        unique=False,
        schema="optimizer",
    )
    op.create_index(
        "ix_microsoft_products_sku_id",
        "microsoft_products",
        ["sku_id"],
        unique=False,
        schema="optimizer",
    )

    # 3. Create microsoft_prices table
    op.create_table(
        "microsoft_prices",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("product_id", sa.String(length=50), nullable=False),
        sa.Column("sku_id", sa.String(length=50), nullable=False),
        sa.Column(
            "market",
            sa.String(length=5),
            nullable=False,
            comment="Market code (ex: AX, FR, US)",
        ),
        sa.Column(
            "currency",
            sa.String(length=3),
            nullable=False,
            comment="ISO 4217 currency code",
        ),
        sa.Column(
            "segment",
            sa.Enum(
                "Commercial",
                "Education",
                "Charity",
                name="pricing_segment",
                schema="optimizer",
            ),
            nullable=False,
        ),
        sa.Column(
            "term_duration",
            sa.String(length=10),
            nullable=False,
            comment="ISO 8601 duration (P1Y=annual, P1M=monthly)",
        ),
        sa.Column(
            "billing_plan",
            sa.Enum("Annual", "Monthly", name="billing_plan", schema="optimizer"),
            nullable=False,
        ),
        sa.Column("unit_price", sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column("erp_price", sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column("effective_start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("effective_end_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "change_indicator",
            sa.String(length=20),
            nullable=False,
            server_default="Unchanged",
        ),
        sa.Column("pricing_tier_range_min", sa.Integer(), nullable=True),
        sa.Column("pricing_tier_range_max", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["product_id", "sku_id"],
            [
                "optimizer.microsoft_products.product_id",
                "optimizer.microsoft_products.sku_id",
            ],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "product_id",
            "sku_id",
            "market",
            "currency",
            "segment",
            "billing_plan",
            "effective_start_date",
            name="uq_price_variant",
        ),
        schema="optimizer",
    )
    op.create_index(
        "ix_microsoft_prices_effective_dates",
        "microsoft_prices",
        ["effective_start_date", "effective_end_date"],
        unique=False,
        schema="optimizer",
    )
    op.create_index(
        "ix_microsoft_prices_product_sku",
        "microsoft_prices",
        ["product_id", "sku_id"],
        unique=False,
        schema="optimizer",
    )
    op.create_index(
        "ix_microsoft_prices_market_currency",
        "microsoft_prices",
        ["market", "currency"],
        unique=False,
        schema="optimizer",
    )


def downgrade() -> None:
    """Drop microsoft pricing tables and types"""
    # Drop tables
    op.drop_table("microsoft_prices", schema="optimizer")
    op.drop_table("microsoft_products", schema="optimizer")

    # Drop types
    op.execute(sa.text("DROP TYPE IF EXISTS optimizer.billing_plan"))
    op.execute(sa.text("DROP TYPE IF EXISTS optimizer.pricing_segment"))
