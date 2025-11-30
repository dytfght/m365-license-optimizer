"""
Add reports table for PDF/Excel report generation
"""
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

# revision identifiers, used by Alembic.
revision = "8a9b7c6d5e4f"
down_revision = "7a1b3c4d5e6f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create reports table
    op.create_table(
        "reports",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("analysis_id", UUID(as_uuid=True), nullable=True),
        sa.Column("tenant_client_id", UUID(as_uuid=True), nullable=False),
        sa.Column("report_type", sa.String(10), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("report_metadata", JSONB(), nullable=False),
        sa.Column("generated_by", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["analysis_id"], ["optimizer.analyses.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_client_id"], ["optimizer.tenant_clients.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="optimizer",
    )

    # Create indexes
    op.create_index(
        "ix_reports_analysis_id",
        "reports",
        ["analysis_id"],
        unique=False,
        schema="optimizer",
    )
    op.create_index(
        "ix_reports_tenant_client_id",
        "reports",
        ["tenant_client_id"],
        unique=False,
        schema="optimizer",
    )
    op.create_index(
        "ix_reports_report_type",
        "reports",
        ["report_type"],
        unique=False,
        schema="optimizer",
    )
    op.create_index(
        "ix_reports_created_at",
        "reports",
        ["created_at"],
        unique=False,
        schema="optimizer",
    )
    op.create_index(
        "ix_reports_expires_at",
        "reports",
        ["expires_at"],
        unique=False,
        schema="optimizer",
    )


def downgrade() -> None:
    # Drop indexes first
    op.drop_index("ix_reports_expires_at", table_name="reports", schema="optimizer")
    op.drop_index("ix_reports_created_at", table_name="reports", schema="optimizer")
    op.drop_index("ix_reports_report_type", table_name="reports", schema="optimizer")
    op.drop_index(
        "ix_reports_tenant_client_id", table_name="reports", schema="optimizer"
    )
    op.drop_index("ix_reports_analysis_id", table_name="reports", schema="optimizer")

    # Drop table
    op.drop_table("reports", schema="optimizer")
