"""Add saved_addresses table

Revision ID: 20241206_add_saved_addresses
Revises: 20241204_130000_add_password_auth
Create Date: 2024-12-06 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20241206_add_saved_addresses'
down_revision: Union[str, None] = '002_add_password_auth'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create saved_addresses table
    op.create_table(
        'saved_addresses',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('address', sa.String(length=500), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=True, server_default='Istanbul'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_saved_addresses_user_id', 'saved_addresses', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_saved_addresses_user_id', table_name='saved_addresses')
    op.drop_table('saved_addresses')

