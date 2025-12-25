"""Add password_changed_at column to users table.

Revision ID: 008_password_changed_at
Revises: 007_email_verification
Create Date: 2024-12-25 14:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "008_password_changed_at"
down_revision: Union[str, None] = "007_email_verification"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add password_changed_at column to users table."""
    op.add_column(
        "users",
        sa.Column(
            "password_changed_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    """Remove password_changed_at column from users table."""
    op.drop_column("users", "password_changed_at")
