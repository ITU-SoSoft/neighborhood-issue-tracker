"""Team model for organizing support staff."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class Team(Base, UUIDMixin, TimestampMixin):
    """Team model representing support team organizations."""

    __tablename__ = "teams"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    members: Mapped[list["User"]] = relationship("User", back_populates="team")
    assigned_tickets: Mapped[list["Ticket"]] = relationship(
        "Ticket", back_populates="assigned_team"
    )
    team_categories: Mapped[list["TeamCategory"]] = relationship(
        "TeamCategory", back_populates="team", cascade="all, delete-orphan"
    )
    team_districts: Mapped[list["TeamDistrict"]] = relationship(
        "TeamDistrict", back_populates="team", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Team {self.name}>"


class TeamCategory(Base):
    """Junction table for team-category assignments."""

    __tablename__ = "team_categories"

    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="CASCADE"),
        primary_key=True,
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    team: Mapped["Team"] = relationship("Team", back_populates="team_categories")
    category: Mapped["Category"] = relationship("Category")


class TeamDistrict(Base):
    """Table for team-district assignments (location-based routing)."""

    __tablename__ = "team_districts"

    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="CASCADE"),
        primary_key=True,
    )
    district_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("districts.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    team: Mapped["Team"] = relationship("Team", back_populates="team_districts")
    district: Mapped["District"] = relationship("District", back_populates="team_assignments")

    def __repr__(self) -> str:
        return f"<TeamDistrict team={self.team_id} district={self.district_id}>"


# Forward references
from app.models.user import User  # noqa: E402, F401
from app.models.ticket import Ticket  # noqa: E402, F401
from app.models.category import Category  # noqa: E402, F401
from app.models.district import District  # noqa: E402, F401
