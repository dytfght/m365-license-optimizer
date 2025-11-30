"""Merge fix_updated_at_cols and reports branches

Revision ID: 94b112f77329
Revises: fix_updated_at_cols, 8a9b7c6d5e4f
Create Date: 2025-11-28 23:55:59.731331

"""
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "94b112f77329"
down_revision: Union[str, Sequence[str], None] = ("fix_updated_at_cols", "8a9b7c6d5e4f")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
