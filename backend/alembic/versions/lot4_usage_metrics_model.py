"""LOT4 - Add UsageMetrics model (table already exists in schema)

Revision ID: lot4_usage_metrics
Revises: lot3_add_password_hash
Create Date: 2025-11-23 20:40:00.000000

Note: The usage_metrics table already exists in the database schema (init.sql).
This migration documents the addition of the UsageMetrics SQLAlchemy model
to the codebase for ORM usage.

"""
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = 'lot4_usage_metrics'
down_revision: Union[str, Sequence[str], None] = 'lot3_add_password_hash'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    The usage_metrics table already exists in the database (created by init.sql).
    This migration is a no-op, documenting that the UsageMetrics ORM model
    has been added to the codebase in LOT4.

    If the table doesn't exist (e.g., in a fresh migration-based setup),
    uncomment the table creation below.
    """
    # Uncomment if table doesn't exist:
    # op.create_table(
    #     'usage_metrics',
    #     sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
    #     sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
    #     sa.Column('period', sa.String(length=10), nullable=False),
    #     sa.Column('report_date', sa.Date(), nullable=False),
    #     sa.Column('last_seen_date', sa.Date(), nullable=True),
    #     sa.Column('email_activity', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    #     sa.Column('onedrive_activity', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    #     sa.Column('sharepoint_activity', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    #     sa.Column('teams_activity', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    #     sa.Column('office_web_activity', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    #     sa.Column('office_desktop_activated', sa.Boolean(), nullable=False),
    #     sa.Column('storage_used_bytes', sa.BigInteger(), nullable=False),
    #     sa.Column('mailbox_size_bytes', sa.BigInteger(), nullable=False),
    #     sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    #     sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    #     sa.ForeignKeyConstraint(['user_id'], ['optimizer.users.id'], ondelete='CASCADE'),
    #     sa.PrimaryKeyConstraint('id'),
    #     sa.UniqueConstraint('user_id', 'period', 'report_date', name='uq_user_period_date'),
    #     schema='optimizer'
    # )
    # op.create_index(op.f('ix_optimizer_usage_metrics_report_date'), 'usage_metrics', ['report_date'], unique=False, schema='optimizer')
    # op.create_index(op.f('ix_optimizer_usage_metrics_user_id'), 'usage_metrics', ['user_id'], unique=False, schema='optimizer')
    pass


def downgrade() -> None:
    """Downgrade schema.

    This is a no-op since the table is managed by init.sql.
    If you created the table via migration, uncomment the drops below.
    """
    # Uncomment if you created the table:
    # op.drop_index(op.f('ix_optimizer_usage_metrics_user_id'), table_name='usage_metrics', schema='optimizer')
    # op.drop_index(op.f('ix_optimizer_usage_metrics_report_date'), table_name='usage_metrics', schema='optimizer')
    # op.drop_table('usage_metrics', schema='optimizer')
    pass
