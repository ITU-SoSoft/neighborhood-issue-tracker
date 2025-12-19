"""Add districts and service_areas tables for location-based team assignment.

Revision ID: 004_districts_service_areas
Revises: 20241206_add_saved_addresses
Create Date: 2024-12-19 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "004_districts_service_areas"
down_revision: Union[str, None] = "20241206_add_saved_addresses"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create districts and service_areas tables."""

    # Create districts table
    op.create_table(
        "districts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
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

    # Create service_areas table (junction table with team, category, district)
    op.create_table(
        "service_areas",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("district_id", postgresql.UUID(as_uuid=True), nullable=False),
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
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["district_id"], ["districts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "team_id",
            "category_id",
            "district_id",
            name="uq_service_area_team_category_district",
        ),
    )

    # Create indexes for faster lookups (using raw SQL for IF NOT EXISTS)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_service_areas_category_district 
        ON service_areas (category_id, district_id)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_service_areas_team 
        ON service_areas (team_id)
        """
    )
    
    # === SEED INITIAL DATA ===
    
    # Insert districts
    op.execute("""
        INSERT INTO districts (id, name, created_at, updated_at) VALUES
        (gen_random_uuid(), 'Kadıköy', now(), now()),
        (gen_random_uuid(), 'Beşiktaş', now(), now()),
        (gen_random_uuid(), 'Şişli', now(), now()),
        (gen_random_uuid(), 'Beyoğlu', now(), now()),
        (gen_random_uuid(), 'Üsküdar', now(), now()),
        (gen_random_uuid(), 'Bakırköy', now(), now()),
        (gen_random_uuid(), 'Fatih', now(), now()),
        (gen_random_uuid(), 'Sarıyer', now(), now()),
        (gen_random_uuid(), 'Maltepe', now(), now()),
        (gen_random_uuid(), 'Ataşehir', now(), now());
    """)
    
    # Insert teams
    op.execute("""
        INSERT INTO teams (id, name, description, created_at, updated_at) VALUES
        (gen_random_uuid(), 'Bakırköy Elektrik Ekibi', 'Bakırköy bölgesi elektrik ve aydınlatma sorunları', now(), now()),
        (gen_random_uuid(), 'Kadıköy Altyapı Ekibi', 'Kadıköy bölgesi altyapı sorunları', now(), now()),
        (gen_random_uuid(), 'Beşiktaş Temizlik Ekibi', 'Beşiktaş bölgesi atık yönetimi ve park bakımı', now(), now()),
        (gen_random_uuid(), 'Genel Destek Ekibi', 'Tüm bölgelerde diğer kategoriler için destek', now(), now());
    """)
    
    # Insert service areas (team-category-district mappings)
    op.execute("""
        INSERT INTO service_areas (id, team_id, category_id, district_id, created_at, updated_at)
        SELECT 
            gen_random_uuid(),
            t.id,
            c.id,
            d.id,
            now(),
            now()
        FROM teams t, categories c, districts d
        WHERE 
            (t.name = 'Bakırköy Elektrik Ekibi' AND c.name = 'Lighting' AND d.name = 'Bakırköy')
            OR (t.name = 'Kadıköy Altyapı Ekibi' AND c.name = 'Infrastructure' AND d.name = 'Kadıköy')
            OR (t.name = 'Kadıköy Altyapı Ekibi' AND c.name = 'Traffic' AND d.name = 'Kadıköy')
            OR (t.name = 'Beşiktaş Temizlik Ekibi' AND c.name = 'Waste Management' AND d.name = 'Beşiktaş')
            OR (t.name = 'Beşiktaş Temizlik Ekibi' AND c.name = 'Parks' AND d.name = 'Beşiktaş')
            OR (t.name = 'Genel Destek Ekibi' AND c.name = 'Other' AND d.name IN ('Kadıköy', 'Beşiktaş', 'Şişli', 'Beyoğlu', 'Üsküdar', 'Bakırköy'));
    """)
    
    # Insert default users (password: manager123! and support123!)
    op.execute("""
        INSERT INTO users (id, phone_number, name, email, password_hash, role, is_verified, is_active, created_at, updated_at) VALUES
        (gen_random_uuid(), '+905001234567', 'Manager User', 'manager@sosoft.com', 
         '$2b$12$0QEC/KYyw27.zLTwKE/Bnu6sUmKUzGWpCmn1lBdHwyPaVrvKFcLAy', 
         'manager', true, true, now(), now()),
        (gen_random_uuid(), '+905001234568', 'Support User', 'support@sosoft.com', 
         '$2b$12$zi0q94K8RRO1pIEizyuo/OYdGRELqbULQmxnz./Uxl5M4Bn4QO3ka', 
         'support', true, true, now(), now());
    """)


def downgrade() -> None:
    """Drop districts and service_areas tables."""
    op.drop_index("ix_service_areas_team", table_name="service_areas")
    op.drop_index("ix_service_areas_category_district", table_name="service_areas")
    op.drop_table("service_areas")
    op.drop_table("districts")

