"""Fix enum values case sensitivity

Revision ID: 951be1c54f01
Revises: e922193f5822
Create Date: 2025-11-30 21:17:31.474884

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '951be1c54f01'
down_revision: Union[str, Sequence[str], None] = 'e922193f5822'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
