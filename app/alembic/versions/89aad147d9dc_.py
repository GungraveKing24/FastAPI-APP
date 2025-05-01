"""empty message

Revision ID: 89aad147d9dc
Revises: 6f3341855639
Create Date: 2025-04-30 23:23:37.426410

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '89aad147d9dc'
down_revision: Union[str, None] = '6f3341855639'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
