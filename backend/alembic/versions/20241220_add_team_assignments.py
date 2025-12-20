"""Add team-based assignment system.

Revision ID: 20241220_add_team_assignments
Revises: 20241206_add_saved_addresses
Create Date: 2024-12-20 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20241220_add_team_assignments"
down_revision: Union[str, None] = "20241206_add_saved_addresses"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add team assignment tables and modify tickets to use team_id instead of assignee_id."""
    
    # Create districts table
    op.create_table(
        "districts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
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
        sa.UniqueConstraint("name", "city", name="uq_district_name_city"),
    )
    
    # Add index for faster lookups
    op.create_index("ix_districts_name_city", "districts", ["name", "city"])
    
    # Create team_categories junction table
    op.create_table(
        "team_categories",
        sa.Column("team_id", sa.UUID(), nullable=False),
        sa.Column("category_id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("team_id", "category_id"),
    )

    # Create team_districts junction table (for location-based assignment)
    op.create_table(
        "team_districts",
        sa.Column("team_id", sa.UUID(), nullable=False),
        sa.Column("district_id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["district_id"], ["districts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("team_id", "district_id"),
    )
    
    # Add index for faster lookups
    op.create_index("ix_team_districts_district_id", "team_districts", ["district_id"])

    # Add team_id to tickets table
    op.add_column(
        "tickets",
        sa.Column("team_id", sa.UUID(), nullable=True),
    )
    
    # Add foreign key constraint
    op.create_foreign_key(
        "fk_tickets_team_id",
        "tickets",
        "teams",
        ["team_id"],
        ["id"],
        ondelete="SET NULL",
    )
    
    # Add index on team_id
    op.create_index("ix_tickets_team_id", "tickets", ["team_id"])

    # Drop assignee_id column and its relationships
    op.drop_constraint("tickets_assignee_id_fkey", "tickets", type_="foreignkey")
    op.drop_column("tickets", "assignee_id")


def downgrade() -> None:
    """Revert team assignment changes."""
    
    # Add back assignee_id
    op.add_column(
        "tickets",
        sa.Column("assignee_id", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "tickets_assignee_id_fkey",
        "tickets",
        "users",
        ["assignee_id"],
        ["id"],
        ondelete="SET NULL",
    )
    
    # Drop team_id
    op.drop_index("ix_tickets_team_id", table_name="tickets")
    op.drop_constraint("fk_tickets_team_id", "tickets", type_="foreignkey")
    op.drop_column("tickets", "team_id")
    
    # Drop team assignment tables
    op.drop_index("ix_team_districts_district_id", table_name="team_districts")
    op.drop_table("team_districts")
    op.drop_table("team_categories")
    
    # Drop districts table
    op.drop_index("ix_districts_name_city", table_name="districts")
    op.drop_table("districts")

