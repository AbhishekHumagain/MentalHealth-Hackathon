"""add forum tables

Revision ID: f1e2d3c4b5a6
Revises: a1253d634e78
Create Date: 2026-03-28 18:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "f1e2d3c4b5a6"
down_revision: Union[str, Sequence[str], None] = "a1253d634e78"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── forum_posts ───────────────────────────────────────────────────────────
    op.create_table(
        "forum_posts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("author_id", sa.String(255), nullable=False),
        sa.Column("author_display_name", sa.String(255), nullable=False),
        sa.Column("is_anonymous", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("anonymous_name", sa.String(100), nullable=False, server_default=""),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("category", sa.String(50), nullable=False, server_default="general"),
        sa.Column("tags", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("likes_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("comments_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column(
            "modified_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("modified_by", sa.String(255), nullable=True),
    )
    op.create_index("ix_forum_posts_author_id", "forum_posts", ["author_id"])
    op.create_index("ix_forum_posts_category", "forum_posts", ["category"])
    op.create_index("ix_forum_posts_created_at", "forum_posts", ["created_at"])

    # ── forum_comments ────────────────────────────────────────────────────────
    op.create_table(
        "forum_comments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "post_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("forum_posts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("author_id", sa.String(255), nullable=False),
        sa.Column("author_display_name", sa.String(255), nullable=False),
        sa.Column("is_anonymous", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("anonymous_name", sa.String(100), nullable=False, server_default=""),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column(
            "modified_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("modified_by", sa.String(255), nullable=True),
    )
    op.create_index("ix_forum_comments_post_id", "forum_comments", ["post_id"])
    op.create_index("ix_forum_comments_author_id", "forum_comments", ["author_id"])

    # ── forum_likes ───────────────────────────────────────────────────────────
    op.create_table(
        "forum_likes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "post_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("forum_posts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("user_id", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_forum_likes_post_id", "forum_likes", ["post_id"])
    op.create_index("ix_forum_likes_user_id", "forum_likes", ["user_id"])
    # Unique: a user can only like a post once
    op.create_unique_constraint("uq_forum_likes_post_user", "forum_likes", ["post_id", "user_id"])

    # ── forum_reports ─────────────────────────────────────────────────────────
    op.create_table(
        "forum_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "post_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("forum_posts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("reporter_id", sa.String(255), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("admin_note", sa.Text(), nullable=False, server_default=""),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column(
            "modified_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("modified_by", sa.String(255), nullable=True),
    )
    op.create_index("ix_forum_reports_post_id", "forum_reports", ["post_id"])
    op.create_index("ix_forum_reports_reporter_id", "forum_reports", ["reporter_id"])
    op.create_index("ix_forum_reports_status", "forum_reports", ["status"])


def downgrade() -> None:
    op.drop_table("forum_reports")
    op.drop_table("forum_likes")
    op.drop_table("forum_comments")
    op.drop_table("forum_posts")
