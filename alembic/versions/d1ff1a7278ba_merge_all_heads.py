"""merge_all_heads

Revision ID: d1ff1a7278ba
Revises: 3f73994aac32, a1b2c3d4e5f6
Create Date: 2026-03-28 14:15:43.787554

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1ff1a7278ba'
down_revision: Union[str, None] = ('3f73994aac32', 'a1b2c3d4e5f6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
