"""
Fix all missing PostgreSQL enum types
Revision ID: fix_enum_types_001
Revises: 23141aeeca2e
Create Date: 2025-11-29 10:00:00.000000
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "fix_enum_types_001"
down_revision = "23141aeeca2e"
branch_labels = None
depends_on = None


def create_enum_type(name: str, values: list):
    """Helper function to create enum type safely"""
    op.execute(
        f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{name}') THEN
                CREATE TYPE {name} AS ENUM ({', '.join([f"'{value}'" for value in values])});
            END IF;
        END$$;
    """
    )


def drop_enum_type(name: str):
    """Helper function to drop enum type"""
    op.execute(f"DROP TYPE IF EXISTS {name} CASCADE")


def upgrade() -> None:
    """Create all missing enum types"""

    # Core enum types used across multiple tables
    create_enum_type("metric_type", ["USAGE", "COST", "EFFICIENCY", "COMPLIANCE"])
    create_enum_type("status_enum", ["ACTIVE", "INACTIVE", "PENDING", "SUSPENDED"])
    create_enum_type("role_enum", ["ADMIN", "USER", "GUEST"])
    create_enum_type(
        "analysis_status_enum", ["PENDING", "RUNNING", "COMPLETED", "FAILED"]
    )
    create_enum_type(
        "report_status_enum", ["PENDING", "GENERATING", "READY", "EXPIRED", "FAILED"]
    )
    create_enum_type("report_format_enum", ["PDF", "EXCEL", "CSV"])
    create_enum_type("tenant_status_enum", ["ACTIVE", "INACTIVE", "SUSPENDED"])

    # LOT8 specific enum types
    create_enum_type("availability_enum", ["AVAILABLE", "UNAVAILABLE", "COMING_SOON"])

    # Fix existing tables that reference these types

    # Fix analytics_metrics table
    op.execute(
        """
        DO $$
        BEGIN
            -- Check if the table exists and has the wrong column type
            IF EXISTS (SELECT 1 FROM information_schema.tables
                      WHERE table_schema = 'optimizer' AND table_name = 'analytics_metrics')
            AND EXISTS (SELECT 1 FROM information_schema.columns
                       WHERE table_schema = 'optimizer' AND table_name = 'analytics_metrics'
                       AND column_name = 'metric_type' AND data_type = 'USER-DEFINED') THEN

                -- Check if it's using the wrong type
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                              WHERE table_schema = 'optimizer' AND table_name = 'analytics_metrics'
                              AND column_name = 'metric_type' AND udt_name = 'metric_type') THEN

                    -- Drop existing constraints and indexes that might reference the column
                    ALTER TABLE optimizer.analytics_metrics DROP CONSTRAINT IF EXISTS analytics_metrics_metric_type_check;

                    -- Alter the column to use the correct enum type
                    ALTER TABLE optimizer.analytics_metrics
                    ALTER COLUMN metric_type TYPE metric_type USING metric_type::text::metric_type;
                END IF;
            END IF;
        END$$;
    """
    )

    # Fix addon_compatibility table for LOT8
    op.execute(
        """
        DO $$
        BEGIN
            -- Check if the table exists and has the wrong column type
            IF EXISTS (SELECT 1 FROM information_schema.tables
                      WHERE table_schema = 'optimizer' AND table_name = 'addon_compatibility')
            AND EXISTS (SELECT 1 FROM information_schema.columns
                       WHERE table_schema = 'optimizer' AND table_name = 'addon_compatibility'
                       AND column_name = 'availability' AND data_type = 'USER-DEFINED') THEN

                -- Check if it's using the wrong type
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                              WHERE table_schema = 'optimizer' AND table_name = 'addon_compatibility'
                              AND column_name = 'availability' AND udt_name = 'availability_enum') THEN

                    -- Drop existing constraints and indexes that might reference the column
                    ALTER TABLE optimizer.addon_compatibility DROP CONSTRAINT IF EXISTS addon_compatibility_availability_check;

                    -- Alter the column to use the correct enum type
                    ALTER TABLE optimizer.addon_compatibility
                    ALTER COLUMN availability TYPE availability_enum USING availability::text::availability_enum;
                END IF;
            END IF;
        END$$;
    """
    )


def downgrade() -> None:
    """Drop all enum types (use with caution)"""

    # Drop LOT8 specific types first
    drop_enum_type("availability_enum")

    # Drop core types (this will fail if they're still being used by tables)
    drop_enum_type("metric_type")
    drop_enum_type("status_enum")
    drop_enum_type("role_enum")
    drop_enum_type("analysis_status_enum")
    drop_enum_type("report_status_enum")
    drop_enum_type("report_format_enum")
    drop_enum_type("tenant_status_enum")
