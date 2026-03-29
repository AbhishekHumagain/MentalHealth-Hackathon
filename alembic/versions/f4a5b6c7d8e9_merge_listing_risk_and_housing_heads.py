"""merge listing risk and housing heads

Revision ID: f4a5b6c7d8e9
Revises: c7d8e9f0a1b2, e3f4a5b6c7d8
Create Date: 2026-03-29 21:30:00.000000

"""

from typing import Sequence, Union


revision: str = "f4a5b6c7d8e9"
down_revision: Union[str, Sequence[str], None] = ("c7d8e9f0a1b2", "e3f4a5b6c7d8")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
