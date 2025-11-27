"""add_analysis_and_recommendation_tables

Revision ID: 7a1b3c4d5e6f
Revises: 6f8a92c3d456
Create Date: 2025-11-27 22:10:00.000000

Adds tables for Lot 6: License optimization based on usage analysis
- analyses: Stores analysis runs with summary and status
- recommendations: Stores individual user-level license recommendations
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '7a1b3c4d5e6f'
down_revision = '6f8a92c3d456'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create analyses and recommendations tables"""
    
    # 1. Create analyses table
    op.create_table(
        'analyses',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_client_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('analysis_date', sa.DateTime(timezone=True), nullable=False, comment='Date and time when analysis was run'),
        sa.Column('status', sa.Enum('PENDING', 'COMPLETED', 'FAILED', name='analysis_status', schema='optimizer'), nullable=False, server_default='PENDING'),
        sa.Column('summary', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}', comment='Analysis summary with totals, costs, savings, and breakdown'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='Error message if status is FAILED'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['tenant_client_id'], ['optimizer.tenant_clients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='optimizer'
    )
    op.create_index('ix_analyses_tenant_client_id', 'analyses', ['tenant_client_id'], unique=False, schema='optimizer')
    op.create_index('ix_analyses_analysis_date', 'analyses', ['analysis_date'], unique=False, schema='optimizer')
    op.create_index('ix_analyses_status', 'analyses', ['status'], unique=False, schema='optimizer')
    
    # 2. Create recommendations table
    op.create_table(
        'recommendations',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('analysis_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('current_sku', sa.String(length=100), nullable=True, comment='Current SKU ID (null if no license)'),
        sa.Column('recommended_sku', sa.String(length=100), nullable=True, comment='Recommended SKU ID (null = remove license)'),
        sa.Column('savings_monthly', sa.DECIMAL(precision=10, scale=2), nullable=False, server_default='0.00', comment='Monthly savings (can be negative for upgrades)'),
        sa.Column('reason', sa.Text(), nullable=False, comment='Explanation for recommendation'),
        sa.Column('status', sa.Enum('PENDING', 'ACCEPTED', 'REJECTED', name='recommendation_status', schema='optimizer'), nullable=False, server_default='PENDING'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['analysis_id'], ['optimizer.analyses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['optimizer.users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='optimizer'
    )
    op.create_index('ix_recommendations_analysis_id', 'recommendations', ['analysis_id'], unique=False, schema='optimizer')
    op.create_index('ix_recommendations_user_id', 'recommendations', ['user_id'], unique=False, schema='optimizer')
    op.create_index('ix_recommendations_status', 'recommendations', ['status'], unique=False, schema='optimizer')


def downgrade() -> None:
    """Drop analyses and recommendations tables"""
    # Drop tables in reverse order (foreign key dependencies)
    op.drop_table('recommendations', schema='optimizer')
    op.drop_table('analyses', schema='optimizer')
    
    # Drop enum types
    op.execute(sa.text('DROP TYPE IF EXISTS optimizer.recommendation_status'))
    op.execute(sa.text('DROP TYPE IF EXISTS optimizer.analysis_status'))
