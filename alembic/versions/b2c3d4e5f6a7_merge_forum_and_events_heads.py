"""merge forum and events heads

Revision ID: b2c3d4e5f6a7
Revises: f1e2d3c4b5a6, 9c1f2a7e4b6d
Create Date: 2026-03-28 23:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = ("f1e2d3c4b5a6", "9c1f2a7e4b6d")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
