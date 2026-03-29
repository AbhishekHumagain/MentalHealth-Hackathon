"""add listing risk fields

Revision ID: c7d8e9f0a1b2
Revises: b2c3d4e5f6a7
Create Date: 2026-03-28 18:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "c7d8e9f0a1b2"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for table_name in ("internships", "events"):
        op.add_column(
            table_name,
            sa.Column("risk_score", sa.Float(), nullable=False, server_default=sa.text("0")),
        )
        op.add_column(
            table_name,
            sa.Column("risk_level", sa.String(length=20), nullable=False, server_default="low"),
        )
        op.add_column(
            table_name,
            sa.Column(
                "risk_reasons",
                postgresql.ARRAY(sa.String()),
                nullable=False,
                server_default=sa.text("ARRAY[]::varchar[]"),
            ),
        )
        op.alter_column(table_name, "risk_score", server_default=None)
        op.alter_column(table_name, "risk_level", server_default=None)
        op.alter_column(table_name, "risk_reasons", server_default=None)


def downgrade() -> None:
    for table_name in ("events", "internships"):
        op.drop_column(table_name, "risk_reasons")
        op.drop_column(table_name, "risk_level")
        op.drop_column(table_name, "risk_score")
