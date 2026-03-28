"""add events table

Revision ID: f6b3d9a2c1e8
Revises: a1253d634e78
Create Date: 2026-03-28 21:15:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "f6b3d9a2c1e8"
down_revision: Union[str, None] = "a1253d634e78"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("hosted_by", sa.String(length=255), nullable=False),
        sa.Column("host_type", sa.String(length=50), nullable=False),
        sa.Column("organizer_name", sa.String(length=255), nullable=False),
        sa.Column("mode", sa.String(length=20), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("meeting_url", sa.String(length=1000), nullable=True),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tags", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "modified_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_events_hosted_by"), "events", ["hosted_by"], unique=False)
    op.create_index(op.f("ix_events_host_type"), "events", ["host_type"], unique=False)
    op.create_index(op.f("ix_events_mode"), "events", ["mode"], unique=False)
    op.create_index(op.f("ix_events_start_at"), "events", ["start_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_events_start_at"), table_name="events")
    op.drop_index(op.f("ix_events_mode"), table_name="events")
    op.drop_index(op.f("ix_events_host_type"), table_name="events")
    op.drop_index(op.f("ix_events_hosted_by"), table_name="events")
    op.drop_table("events")
