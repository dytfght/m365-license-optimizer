"""
Fix updated_at columns for license_assignments and usage_metrics tables
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fix_updated_at_cols'
down_revision = '7a1b3c4d5e6f'  # dernière migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ajouter updated_at à license_assignments
    op.add_column(
        'license_assignments',
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        schema='optimizer'
    )
    
    # Ajouter updated_at à usage_metrics
    op.add_column(
        'usage_metrics',
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        schema='optimizer'
    )


def downgrade() -> None:
    # Supprimer updated_at de license_assignments
    op.drop_column('license_assignments', 'updated_at', schema='optimizer')
    
    # Supprimer updated_at de usage_metrics
    op.drop_column('usage_metrics', 'updated_at', schema='optimizer')