"""add external internship metadata

Revision ID: 74b9d3df66c3
Revises: a1b2c3d4e5f6
Create Date: 2026-03-28 03:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "74b9d3df66c3"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("internships", sa.Column("external_id", sa.String(length=255), nullable=True))
    op.add_column("internships", sa.Column("source_name", sa.String(length=100), nullable=True))
    op.add_column("internships", sa.Column("source_url", sa.String(length=1000), nullable=True))
    op.add_column("internships", sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True))
    op.create_unique_constraint(
        "uq_internship_source_external_id",
        "internships",
        ["source_name", "external_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_internship_source_external_id", "internships", type_="unique")
    op.drop_column("internships", "last_seen_at")
    op.drop_column("internships", "source_url")
    op.drop_column("internships", "source_name")
    op.drop_column("internships", "external_id")
