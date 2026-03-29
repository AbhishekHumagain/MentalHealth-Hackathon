"""add external apartment metadata

Revision ID: e3f4a5b6c7d8
Revises: b2c3d4e5f6a7
Create Date: 2026-03-29 08:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "e3f4a5b6c7d8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "apartments",
        sa.Column("source_type", sa.String(length=50), nullable=False, server_default="manual"),
    )
    op.add_column("apartments", sa.Column("external_id", sa.String(length=255), nullable=True))
    op.add_column("apartments", sa.Column("source_name", sa.String(length=100), nullable=True))
    op.add_column("apartments", sa.Column("source_url", sa.String(length=1000), nullable=True))
    op.add_column("apartments", sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("apartments", sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("apartments", sa.Column("raw_payload", sa.JSON(), nullable=True))
    op.alter_column("apartments", "contact_email", existing_type=sa.String(length=255), nullable=True)
    op.create_unique_constraint(
        "uq_apartment_source_external_id",
        "apartments",
        ["source_name", "external_id"],
    )
    op.create_index(op.f("ix_apartments_source_name"), "apartments", ["source_name"], unique=False)
    op.create_index(op.f("ix_apartments_external_id"), "apartments", ["external_id"], unique=False)
    op.alter_column("apartments", "source_type", server_default=None)


def downgrade() -> None:
    op.drop_index(op.f("ix_apartments_external_id"), table_name="apartments")
    op.drop_index(op.f("ix_apartments_source_name"), table_name="apartments")
    op.drop_constraint("uq_apartment_source_external_id", "apartments", type_="unique")
    op.alter_column("apartments", "contact_email", existing_type=sa.String(length=255), nullable=False)
    op.drop_column("apartments", "raw_payload")
    op.drop_column("apartments", "last_seen_at")
    op.drop_column("apartments", "first_seen_at")
    op.drop_column("apartments", "source_url")
    op.drop_column("apartments", "source_name")
    op.drop_column("apartments", "external_id")
    op.drop_column("apartments", "source_type")
