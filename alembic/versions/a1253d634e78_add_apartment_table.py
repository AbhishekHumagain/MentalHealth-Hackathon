"""add_apartment_table

Revision ID: a1253d634e78
Revises: d1ff1a7278ba
Create Date: 2026-03-28 14:15:57.868961

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1253d634e78'
down_revision: Union[str, None] = 'd1ff1a7278ba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('apartments',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('address', sa.String(length=255), nullable=False),
    sa.Column('city', sa.String(length=100), nullable=False),
    sa.Column('state', sa.String(length=100), nullable=False),
    sa.Column('zip_code', sa.String(length=20), nullable=False),
    sa.Column('monthly_rent', sa.Float(), nullable=False),
    sa.Column('bedrooms', sa.Integer(), nullable=False),
    sa.Column('bathrooms', sa.Float(), nullable=False),
    sa.Column('is_furnished', sa.Boolean(), nullable=False),
    sa.Column('is_available', sa.Boolean(), nullable=False),
    sa.Column('available_from', sa.String(length=50), nullable=True),
    sa.Column('images_urls', postgresql.ARRAY(sa.String()), nullable=False),
    sa.Column('amenities', postgresql.ARRAY(sa.String()), nullable=False),
    sa.Column('posted_by', sa.String(length=36), nullable=False),
    sa.Column('contact_email', sa.String(length=255), nullable=False),
    sa.Column('contact_phone', sa.String(length=50), nullable=True),
    sa.Column('is_deleted', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('modified_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_apartments_city'), 'apartments', ['city'], unique=False)
    op.create_index(op.f('ix_apartments_state'), 'apartments', ['state'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_apartments_state'), table_name='apartments')
    op.drop_index(op.f('ix_apartments_city'), table_name='apartments')
    op.drop_table('apartments')
