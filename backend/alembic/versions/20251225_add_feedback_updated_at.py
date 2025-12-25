"""Add updated_at to feedback table

Revision ID: add_feedback_updated_at
Revises: add_new_notification_types
Create Date: 2025-12-25 19:10:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "add_feedback_updated_at"
down_revision: Union[str, None] = "add_new_notification_types"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if column already exists to make migration idempotent
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='feedbacks' AND column_name='updated_at'"
        )
    )
    if result.fetchone() is None:
        op.add_column(
            "feedbacks",
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        )


def downgrade() -> None:
    op.drop_column("feedbacks", "updated_at")
