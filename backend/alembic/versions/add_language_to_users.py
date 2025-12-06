"""add language to users

Revision ID: add_language_to_users
Revises: f3a60987c211
Create Date: 2025-12-06 18:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_language_to_users'
down_revision: Union[str, Sequence[str], None] = 'f3a60987c211'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add language column to users table"""
    op.add_column(
        'users',
        sa.Column('language', sa.String(length=5), nullable=False, server_default='en'),
        schema='optimizer'
    )
    # Remove server_default after adding the column
    op.alter_column('users', 'language', server_default=None, schema='optimizer')


def downgrade() -> None:
    """Remove language column from users table"""
    op.drop_column('users', 'language', schema='optimizer')
