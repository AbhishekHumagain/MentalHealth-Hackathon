"""merge images and risk heads

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8, f4a5b6c7d8e9
Create Date: 2026-03-28 23:45:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = ("c3d4e5f6a7b8", "f4a5b6c7d8e9")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
