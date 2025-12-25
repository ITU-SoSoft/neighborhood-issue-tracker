"""Allow multiple escalations per ticket for history tracking.

Revision ID: 20241222_multi_escalations
Revises: 20241220_add_team_assignments
Create Date: 2024-12-22 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20241222_multi_escalations"
down_revision: Union[str, None] = "20241220_add_team_assignments"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove unique constraint on ticket_id to allow multiple escalations per ticket."""
    # Check if constraint exists before trying to drop it
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT constraint_name FROM information_schema.table_constraints "
            "WHERE table_name = 'escalation_requests' "
            "AND constraint_name = 'escalation_requests_ticket_id_key'"
        )
    )
    if result.fetchone() is not None:
        op.drop_constraint(
            "escalation_requests_ticket_id_key",
            "escalation_requests",
            type_="unique",
        )


def downgrade() -> None:
    """Re-add unique constraint on ticket_id (only works if no duplicate ticket_ids exist)."""
    op.create_unique_constraint(
        "escalation_requests_ticket_id_key",
        "escalation_requests",
        ["ticket_id"],
    )
