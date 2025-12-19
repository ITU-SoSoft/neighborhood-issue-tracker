"""Initial schema migration.

Revision ID: 001_initial
Revises:
Create Date: 2024-12-04 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all initial tables."""

    # Enable PostGIS extension
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # Create enums
    userrole_enum = postgresql.ENUM(
        "citizen", "support", "manager", name="userrole", create_type=False
    )
    userrole_enum.create(op.get_bind(), checkfirst=True)

    ticketstatus_enum = postgresql.ENUM(
        "new",
        "in_progress",
        "resolved",
        "closed",
        "escalated",
        name="ticketstatus",
        create_type=False,
    )
    ticketstatus_enum.create(op.get_bind(), checkfirst=True)

    phototype_enum = postgresql.ENUM(
        "report", "proof", name="phototype", create_type=False
    )
    phototype_enum.create(op.get_bind(), checkfirst=True)

    escalationstatus_enum = postgresql.ENUM(
        "pending", "approved", "rejected", name="escalationstatus", create_type=False
    )
    escalationstatus_enum.create(op.get_bind(), checkfirst=True)

    # Create teams table
    op.create_table(
        "teams",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
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
        sa.UniqueConstraint("name"),
    )

    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("phone_number", sa.String(length=15), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column(
            "role",
            userrole_enum,
            nullable=False,
            server_default="citizen",
        ),
        sa.Column("team_id", sa.UUID(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
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
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_users_phone_number"), "users", ["phone_number"], unique=True
    )

    # Create otp_codes table
    op.create_table(
        "otp_codes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("phone_number", sa.String(length=15), nullable=False),
        sa.Column("code", sa.String(length=6), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_used", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_otp_codes_phone_number"), "otp_codes", ["phone_number"])

    # Create categories table
    op.create_table(
        "categories",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
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
        sa.UniqueConstraint("name"),
    )

    # Create locations table (with PostGIS)
    op.create_table(
        "locations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "coordinates",
            Geometry(geometry_type="POINT", srid=4326, from_text="ST_GeomFromEWKT"),
            nullable=False,
        ),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("address", sa.String(length=500), nullable=True),
        sa.Column("district", sa.String(length=100), nullable=True),
        sa.Column(
            "city", sa.String(length=100), nullable=False, server_default="Istanbul"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # Create spatial index on coordinates (using raw SQL for IF NOT EXISTS)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_locations_coordinates 
        ON locations USING gist (coordinates)
        """
    )
    
    # === SEED INITIAL DATA ===
    # Insert default categories
    op.execute("""
        INSERT INTO categories (id, name, description, is_active, created_at, updated_at) VALUES
        (gen_random_uuid(), 'Infrastructure', 'Road damage, sidewalk issues, building problems', true, now(), now()),
        (gen_random_uuid(), 'Traffic', 'Traffic signals, road signs, pedestrian crossings', true, now(), now()),
        (gen_random_uuid(), 'Lighting', 'Street lights, park lighting, public area illumination', true, now(), now()),
        (gen_random_uuid(), 'Waste Management', 'Garbage collection, recycling, illegal dumping', true, now(), now()),
        (gen_random_uuid(), 'Parks', 'Park maintenance, playgrounds, green spaces', true, now(), now()),
        (gen_random_uuid(), 'Other', 'General neighborhood issues not in other categories', true, now(), now());
    """)

    # Create tickets table
    op.create_table(
        "tickets",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "status",
            ticketstatus_enum,
            nullable=False,
            server_default="new",
        ),
        sa.Column("category_id", sa.UUID(), nullable=False),
        sa.Column("location_id", sa.UUID(), nullable=False),
        sa.Column("reporter_id", sa.UUID(), nullable=False),
        sa.Column("assignee_id", sa.UUID(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["category_id"], ["categories.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reporter_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assignee_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tickets_status"), "tickets", ["status"])

    # Create ticket_followers table (junction table)
    op.create_table(
        "ticket_followers",
        sa.Column("ticket_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column(
            "followed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("ticket_id", "user_id"),
    )

    # Create status_logs table
    op.create_table(
        "status_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("ticket_id", sa.UUID(), nullable=False),
        sa.Column("old_status", sa.String(length=50), nullable=True),
        sa.Column("new_status", sa.String(length=50), nullable=False),
        sa.Column("changed_by_id", sa.UUID(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["changed_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create photos table
    op.create_table(
        "photos",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("ticket_id", sa.UUID(), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column(
            "photo_type",
            phototype_enum,
            nullable=False,
            server_default="report",
        ),
        sa.Column("uploaded_by_id", sa.UUID(), nullable=True),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create comments table
    op.create_table(
        "comments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("ticket_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_internal", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create feedbacks table
    op.create_table(
        "feedbacks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("ticket_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name="check_rating_range"),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticket_id"),
    )

    # Create escalation_requests table
    op.create_table(
        "escalation_requests",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("ticket_id", sa.UUID(), nullable=False),
        sa.Column("requester_id", sa.UUID(), nullable=True),
        sa.Column("reviewer_id", sa.UUID(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "status",
            escalationstatus_enum,
            nullable=False,
            server_default="pending",
        ),
        sa.Column("review_comment", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticket_id"),
    )


def downgrade() -> None:
    """Drop all tables in reverse order."""
    op.drop_table("escalation_requests")
    op.drop_table("feedbacks")
    op.drop_table("comments")
    op.drop_table("photos")
    op.drop_table("status_logs")
    op.drop_table("ticket_followers")
    op.drop_table("tickets")
    op.drop_index(
        "idx_locations_coordinates", table_name="locations", postgresql_using="gist"
    )
    op.drop_table("locations")
    op.drop_table("categories")
    op.drop_index(op.f("ix_otp_codes_phone_number"), table_name="otp_codes")
    op.drop_table("otp_codes")
    op.drop_index(op.f("ix_users_phone_number"), table_name="users")
    op.drop_table("users")
    op.drop_table("teams")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS escalationstatus")
    op.execute("DROP TYPE IF EXISTS phototype")
    op.execute("DROP TYPE IF EXISTS ticketstatus")
    op.execute("DROP TYPE IF EXISTS userrole")

    # Drop PostGIS extension (optional, usually keep it)
    # op.execute("DROP EXTENSION IF EXISTS postgis")
