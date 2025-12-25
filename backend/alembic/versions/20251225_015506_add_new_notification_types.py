"""add new notification types

Revision ID: add_new_notification_types
Revises: 20241223_add_notifications
Create Date: 2025-12-25 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_new_notification_types'
down_revision: Union[str, None] = '20241223_add_notifications'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new notification types to the enum (one at a time)
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'ESCALATION_REQUESTED'")
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'ESCALATION_APPROVED'")
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'ESCALATION_REJECTED'")
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'NEW_TICKET_FOR_TEAM'")


def downgrade() -> None:
    # Note: PostgreSQL doesn't support removing enum values
    # This would require recreating the enum type
    pass
