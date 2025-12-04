"""Add password authentication fields.

Revision ID: 002_add_password_auth
Revises: 001_initial
Create Date: 2024-12-04 13:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002_add_password_auth"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add password_hash column and make email required with unique constraint."""
    # Add password_hash column
    op.add_column(
        "users",
        sa.Column(
            "password_hash", sa.String(length=255), nullable=False, server_default=""
        ),
    )

    # Remove the server default after column is created (it was just for migration)
    op.alter_column("users", "password_hash", server_default=None)

    # Make email non-nullable (assuming no existing users as per requirements)
    op.alter_column(
        "users",
        "email",
        existing_type=sa.String(length=255),
        nullable=False,
        server_default="",
    )
    op.alter_column("users", "email", server_default=None)

    # Add unique index on email
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)


def downgrade() -> None:
    """Remove password_hash column and revert email changes."""
    # Drop unique index on email
    op.drop_index(op.f("ix_users_email"), table_name="users")

    # Make email nullable again
    op.alter_column(
        "users",
        "email",
        existing_type=sa.String(length=255),
        nullable=True,
    )

    # Drop password_hash column
    op.drop_column("users", "password_hash")
