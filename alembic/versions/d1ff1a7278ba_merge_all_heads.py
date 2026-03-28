"""merge_all_heads

Revision ID: d1ff1a7278ba
Revises: c4f8be8c0c2a
Create Date: 2026-03-28 14:15:43.787554

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1ff1a7278ba'
down_revision: Union[str, None] = 'c4f8be8c0c2a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
