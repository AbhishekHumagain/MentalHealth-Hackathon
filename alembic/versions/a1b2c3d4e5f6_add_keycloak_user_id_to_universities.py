"""add keycloak_user_id to universities

Revision ID: a1b2c3d4e5f6
Revises: 2f6d5b0afadd
Create Date: 2026-03-28 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "2f6d5b0afadd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "universities",
        sa.Column("keycloak_user_id", sa.String(length=255), nullable=True),
    )
    op.create_unique_constraint(
        "uq_universities_keycloak_user_id",
        "universities",
        ["keycloak_user_id"],
    )
    op.create_index(
        op.f("ix_universities_keycloak_user_id"),
        "universities",
        ["keycloak_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_universities_keycloak_user_id"), table_name="universities")
    op.drop_constraint(
        "uq_universities_keycloak_user_id",
        "universities",
        type_="unique",
    )
    op.drop_column("universities", "keycloak_user_id")
