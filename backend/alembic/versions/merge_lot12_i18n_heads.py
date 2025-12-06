"""merge lot12 i18n heads

Revision ID: merge_lot12_i18n_heads
Revises: 54ffcbb7ee60, add_language_to_users
Create Date: 2025-12-06 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'merge_lot12_i18n_heads'
down_revision: Union[str, Sequence[str], None] = ('54ffcbb7ee60', 'add_language_to_users')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge the i18n branch with main branch"""
    pass


def downgrade() -> None:
    """Downgrade merge revision"""
    pass
