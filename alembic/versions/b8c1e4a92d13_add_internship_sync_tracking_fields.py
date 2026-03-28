"""add internship sync tracking fields

Revision ID: b8c1e4a92d13
Revises: a1b2c3d4e5f6
Create Date: 2026-03-28 13:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b8c1e4a92d13"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("internships", sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("internships", sa.Column("raw_payload", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("internships", "raw_payload")
    op.drop_column("internships", "first_seen_at")
