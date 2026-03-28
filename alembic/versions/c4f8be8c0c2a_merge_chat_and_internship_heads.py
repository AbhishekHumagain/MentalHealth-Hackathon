"""merge chat and internship heads

Revision ID: c4f8be8c0c2a
Revises: 3f73994aac32, b8c1e4a92d13
Create Date: 2026-03-28 19:05:00.000000

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "c4f8be8c0c2a"
down_revision: Union[str, Sequence[str], None] = ("3f73994aac32", "b8c1e4a92d13")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
