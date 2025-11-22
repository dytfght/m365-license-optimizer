"""add password_hash to users

Revision ID: lot3_add_password_hash
Revises: 5b0d2cfdd9c8
Create Date: 2025-11-22 19:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'lot3_add_password_hash'
down_revision: Union[str, None] = '5b0d2cfdd9c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add password_hash column to users table for authentication"""
    op.add_column(
        'users',
        sa.Column('password_hash', sa.String(length=255), nullable=True, comment='Hashed password for authentication (partner users only)'),
        schema='optimizer'
    )


def downgrade() -> None:
    """Remove password_hash column from users table"""
    op.drop_column('users', 'password_hash', schema='optimizer')
