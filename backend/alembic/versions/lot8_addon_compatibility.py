"""lot8_addon_compatibility

Revision ID: 8f9e0d1c2b3a
Revises: 7a1b3c4d5e6f
Create Date: 2025-11-28 10:00:00.000000

Adds tables for Lot 8: SKU mapping and add-on compatibility management
- addon_compatibility: Maps add-ons to their compatible base SKUs
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "8f9e0d1c2b3a"
down_revision = "7a1b3c4d5e6f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create addon_compatibility table"""

    # Create addon_compatibility table
    op.create_table(
        "addon_compatibility",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "addon_sku_id",
            sa.String(length=50),
            nullable=False,
            comment="Partner Center SKU ID for the add-on",
        ),
        sa.Column(
            "addon_product_id",
            sa.String(length=50),
            nullable=False,
            comment="Partner Center Product ID for the add-on",
        ),
        sa.Column(
            "base_sku_id",
            sa.String(length=50),
            nullable=False,
            comment="Partner Center SKU ID for compatible base SKU",
        ),
        sa.Column(
            "base_product_id",
            sa.String(length=50),
            nullable=False,
            comment="Partner Center Product ID for compatible base SKU",
        ),
        sa.Column(
            "service_type",
            sa.String(length=100),
            nullable=False,
            comment='Service type (e.g., "Microsoft 365", "Dynamics 365")',
        ),
        sa.Column(
            "addon_category",
            sa.String(length=100),
            nullable=False,
            comment='Category of add-on (e.g., "Storage", "Calling Plan")',
        ),
        sa.Column(
            "min_quantity",
            sa.Integer(),
            nullable=False,
            server_default="1",
            comment="Minimum quantity required",
        ),
        sa.Column(
            "max_quantity",
            sa.Integer(),
            nullable=True,
            comment="Maximum quantity allowed (null = unlimited)",
        ),
        sa.Column(
            "quantity_multiplier",
            sa.Integer(),
            nullable=False,
            server_default="1",
            comment="Quantity must be multiple of this value",
        ),
        sa.Column(
            "requires_domain_validation",
            sa.Boolean(),
            nullable=False,
            server_default="false",
            comment="Requires domain-level validation",
        ),
        sa.Column(
            "requires_tenant_validation",
            sa.Boolean(),
            nullable=False,
            server_default="false",
            comment="Requires tenant-level validation",
        ),
        sa.Column(
            "validation_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Additional validation metadata",
        ),
        sa.Column(
            "pc_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Partner Center specific metadata",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default="true",
            comment="Whether this mapping is active",
        ),
        sa.Column(
            "effective_date",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Date when this mapping becomes effective",
        ),
        sa.Column(
            "expiration_date",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Date when this mapping expires",
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
            comment="Description of the compatibility mapping",
        ),
        sa.Column(
            "notes",
            sa.Text(),
            nullable=True,
            comment="Internal notes about this mapping",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="optimizer",
    )

    # Create indexes
    op.create_index(
        "ix_addon_compatibility_addon_sku_id",
        "addon_compatibility",
        ["addon_sku_id"],
        unique=False,
        schema="optimizer",
    )
    op.create_index(
        "ix_addon_compatibility_base_sku_id",
        "addon_compatibility",
        ["base_sku_id"],
        unique=False,
        schema="optimizer",
    )
    op.create_index(
        "ix_addon_compatibility_service_type",
        "addon_compatibility",
        ["service_type"],
        unique=False,
        schema="optimizer",
    )
    op.create_index(
        "ix_addon_compatibility_addon_category",
        "addon_compatibility",
        ["addon_category"],
        unique=False,
        schema="optimizer",
    )
    op.create_index(
        "ix_addon_compatibility_is_active",
        "addon_compatibility",
        ["is_active"],
        unique=False,
        schema="optimizer",
    )
    op.create_index(
        "ix_addon_compatibility_created_at",
        "addon_compatibility",
        ["created_at"],
        unique=False,
        schema="optimizer",
    )


def downgrade() -> None:
    """Drop addon_compatibility table and indexes"""
    # Drop indexes first
    op.drop_index(
        "ix_addon_compatibility_created_at",
        table_name="addon_compatibility",
        schema="optimizer",
    )
    op.drop_index(
        "ix_addon_compatibility_is_active",
        table_name="addon_compatibility",
        schema="optimizer",
    )
    op.drop_index(
        "ix_addon_compatibility_addon_category",
        table_name="addon_compatibility",
        schema="optimizer",
    )
    op.drop_index(
        "ix_addon_compatibility_service_type",
        table_name="addon_compatibility",
        schema="optimizer",
    )
    op.drop_index(
        "ix_addon_compatibility_base_sku_id",
        table_name="addon_compatibility",
        schema="optimizer",
    )
    op.drop_index(
        "ix_addon_compatibility_addon_sku_id",
        table_name="addon_compatibility",
        schema="optimizer",
    )

    # Drop table
    op.drop_table("addon_compatibility", schema="optimizer")
