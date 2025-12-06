"""Fix license_assignment enum types to match model

Revision ID: e922193f5822
Revises: fix_enum_types_001
Create Date: 2025-11-30 21:16:19.506378

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = 'e922193f5822'
down_revision = 'fix_enum_types_001'
branch_labels = None
depends_on = None


def create_enum_type(name: str, values: list, schema: str = "optimizer"):
    """Helper function to create enum type safely"""
    op.execute(
        f"""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_type t
                JOIN pg_namespace n ON n.oid = t.typnamespace
                WHERE t.typname = '{name}' AND n.nspname = '{schema}'
            ) THEN
                CREATE TYPE {schema}.{name} AS ENUM ({', '.join([f"'{value}'" for value in values])});
            END IF;
        END$$;
    """
    )


def drop_enum_type(name: str, schema: str = "optimizer"):
    """Helper function to drop enum type"""
    op.execute(f"DROP TYPE IF EXISTS {schema}.{name} CASCADE")


def upgrade() -> None:
    """Create/Fix license_assignment enum types"""

    # Create license_status enum if it doesn't exist
    create_enum_type(
        "license_status",
        ["active", "suspended", "disabled", "trial"]
    )

    # Create assignment_source enum if it doesn't exist
    create_enum_type(
        "assignment_source",
        ["manual", "auto", "group_policy"]
    )

    # Verify and fix license_assignments table columns
    op.execute(
        """
        DO $$
        BEGIN
            -- Check if license_assignments table exists and has status column
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'optimizer' AND table_name = 'license_assignments'
            ) AND EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'optimizer' AND table_name = 'license_assignments'
                AND column_name = 'status'
            ) THEN

                -- Check if status column is using the correct enum type
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'optimizer' AND table_name = 'license_assignments'
                    AND column_name = 'status' AND udt_name = 'license_status'
                ) THEN

                    -- Convert status column to use license_status enum
                    ALTER TABLE optimizer.license_assignments
                    ALTER COLUMN status TYPE optimizer.license_status
                    USING status::text::optimizer.license_status;

                END IF;
            END IF;
        END$$;
        """
    )

    # Verify and fix source column
    op.execute(
        """
        DO $$
        BEGIN
            -- Check if license_assignments table exists and has source column
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'optimizer' AND table_name = 'license_assignments'
            ) AND EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'optimizer' AND table_name = 'license_assignments'
                AND column_name = 'source'
            ) THEN

                -- Check if source column is using the correct enum type
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'optimizer' AND table_name = 'license_assignments'
                    AND column_name = 'source' AND udt_name = 'assignment_source'
                ) THEN

                    -- Convert source column to use assignment_source enum
                    ALTER TABLE optimizer.license_assignments
                    ALTER COLUMN source TYPE optimizer.assignment_source
                    USING source::text::optimizer.assignment_source;

                END IF;
            END IF;
        END$$;
        """
    )


def downgrade() -> None:
    """Drop enum types (use with caution)"""

    # Note: This will fail if the types are still being used by tables
    op.execute("ALTER TABLE optimizer.license_assignments ALTER COLUMN status TYPE text")
    op.execute("ALTER TABLE optimizer.license_assignments ALTER COLUMN source TYPE text")

    drop_enum_type("license_status")
    drop_enum_type("assignment_source")
