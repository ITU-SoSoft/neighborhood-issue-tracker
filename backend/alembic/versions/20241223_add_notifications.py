"""Add notifications table.

Revision ID: 20241223_add_notifications
Revises: 20241222_multi_escalations
Create Date: 2024-12-23 06:30:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20241223_add_notifications"
down_revision: Union[str, None] = "20241222_multi_escalations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create notifications table."""
    bind = op.get_bind()
    inspector = inspect(bind)

    # Create NotificationType enum
    notificationtype_enum = postgresql.ENUM(
        "TICKET_CREATED",
        "TICKET_STATUS_CHANGED",
        "TICKET_FOLLOWED",
        "COMMENT_ADDED",
        "TICKET_ASSIGNED",
        name="notificationtype",
        create_type=False,
    )
    notificationtype_enum.create(bind, checkfirst=True)

    # Create notifications table only if it doesn't exist
    if "notifications" not in inspector.get_table_names():
        op.create_table(
            "notifications",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column(
                "user_id",
                sa.UUID(),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "ticket_id",
                sa.UUID(),
                sa.ForeignKey("tickets.id", ondelete="CASCADE"),
                nullable=True,
            ),
            sa.Column(
                "notification_type",
                notificationtype_enum,
                nullable=False,
            ),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
        )

    # Create indexes only if they don't exist
    existing_indexes = {idx["name"] for idx in inspector.get_indexes("notifications")}

    if "ix_notifications_user_id" not in existing_indexes:
        op.create_index(
            "ix_notifications_user_id",
            "notifications",
            ["user_id"],
        )
    if "ix_notifications_is_read" not in existing_indexes:
        op.create_index(
            "ix_notifications_is_read",
            "notifications",
            ["is_read"],
        )


def downgrade() -> None:
    """Drop notifications table."""
    op.drop_index("ix_notifications_is_read", table_name="notifications")
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")

    # Drop enum
    notificationtype_enum = postgresql.ENUM(name="notificationtype")
    notificationtype_enum.drop(op.get_bind(), checkfirst=True)
