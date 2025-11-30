"""Merge multiple heads

Revision ID: 23141aeeca2e
Revises: f3a60987c211, 8f9e0d1c2b3a
Create Date: 2025-11-29 09:20:42.134867

"""
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "23141aeeca2e"
down_revision: Union[str, Sequence[str], None] = ("f3a60987c211", "8f9e0d1c2b3a")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
