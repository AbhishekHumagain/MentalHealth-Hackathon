"""add internship matching models

Revision ID: 2f6d5b0afadd
Revises: 51f8c8c34e5c
Create Date: 2026-03-28 01:40:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "2f6d5b0afadd"
down_revision: Union[str, None] = "51f8c8c34e5c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "student_profiles",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("university_id", sa.UUID(), nullable=False),
        sa.Column("major", sa.String(length=255), nullable=False),
        sa.Column("skills", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("interests", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("graduation_year", sa.Integer(), nullable=True),
        sa.Column("preferred_locations", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("modified_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["university_id"], ["universities.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_student_profiles_major"), "student_profiles", ["major"], unique=False)
    op.create_index(op.f("ix_student_profiles_university_id"), "student_profiles", ["university_id"], unique=False)
    op.create_index(op.f("ix_student_profiles_user_id"), "student_profiles", ["user_id"], unique=False)

    op.create_table(
        "internships",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("company", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=False),
        sa.Column("application_url", sa.String(length=1000), nullable=False),
        sa.Column("posted_by", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("majors", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("keywords", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("modified_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_internships_company"), "internships", ["company"], unique=False)
    op.create_index(op.f("ix_internships_posted_by"), "internships", ["posted_by"], unique=False)
    op.create_index(op.f("ix_internships_title"), "internships", ["title"], unique=False)

    op.create_table(
        "internship_recommendations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("student_profile_id", sa.UUID(), nullable=False),
        sa.Column("internship_id", sa.UUID(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("recommended_for_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["internship_id"], ["internships.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_profile_id"], ["student_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "student_profile_id",
            "internship_id",
            "recommended_for_date",
            name="uq_profile_internship_day",
        ),
    )
    op.create_index(
        op.f("ix_internship_recommendations_internship_id"),
        "internship_recommendations",
        ["internship_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_internship_recommendations_recommended_for_date"),
        "internship_recommendations",
        ["recommended_for_date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_internship_recommendations_student_profile_id"),
        "internship_recommendations",
        ["student_profile_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_internship_recommendations_student_profile_id"), table_name="internship_recommendations")
    op.drop_index(op.f("ix_internship_recommendations_recommended_for_date"), table_name="internship_recommendations")
    op.drop_index(op.f("ix_internship_recommendations_internship_id"), table_name="internship_recommendations")
    op.drop_table("internship_recommendations")

    op.drop_index(op.f("ix_internships_title"), table_name="internships")
    op.drop_index(op.f("ix_internships_posted_by"), table_name="internships")
    op.drop_index(op.f("ix_internships_company"), table_name="internships")
    op.drop_table("internships")

    op.drop_index(op.f("ix_student_profiles_user_id"), table_name="student_profiles")
    op.drop_index(op.f("ix_student_profiles_university_id"), table_name="student_profiles")
    op.drop_index(op.f("ix_student_profiles_major"), table_name="student_profiles")
    op.drop_table("student_profiles")
