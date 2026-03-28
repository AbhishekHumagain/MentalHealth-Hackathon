"""add event rsvps table

Revision ID: 9c1f2a7e4b6d
Revises: f6b3d9a2c1e8
Create Date: 2026-03-28 22:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "9c1f2a7e4b6d"
down_revision: Union[str, None] = "f6b3d9a2c1e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "event_rsvps",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
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
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", "user_id", name="uq_event_rsvp_event_user"),
    )
    op.create_index(op.f("ix_event_rsvps_event_id"), "event_rsvps", ["event_id"], unique=False)
    op.create_index(op.f("ix_event_rsvps_user_id"), "event_rsvps", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_event_rsvps_user_id"), table_name="event_rsvps")
    op.drop_index(op.f("ix_event_rsvps_event_id"), table_name="event_rsvps")
    op.drop_table("event_rsvps")
