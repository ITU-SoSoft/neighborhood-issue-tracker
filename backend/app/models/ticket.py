"""Ticket and related models."""

import enum
import uuid
from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin, UUIDMixin


class TicketStatus(str, enum.Enum):
    """Ticket status enumeration."""

    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    ESCALATED = "ESCALATED"


class Location(Base, UUIDMixin):
    """Location model with PostGIS support."""

    __tablename__ = "locations"

    # PostGIS point geometry (SRID 4326 = WGS84)
    coordinates: Mapped[str] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326),
        nullable=False,
    )
    # Store lat/lng separately for easier access
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str] = mapped_column(String(100), default="Istanbul", nullable=False)

    # Relationship
    ticket: Mapped["Ticket"] = relationship(
        "Ticket", back_populates="location", uselist=False
    )

    def __repr__(self) -> str:
        return f"<Location ({self.latitude}, {self.longitude})>"


class Ticket(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Ticket model representing reported issues."""

    __tablename__ = "tickets"

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[TicketStatus] = mapped_column(
        Enum(TicketStatus),
        default=TicketStatus.NEW,
        nullable=False,
        index=True,
    )

    # Foreign keys
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="CASCADE"),
        nullable=False,
    )
    reporter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    team_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    category: Mapped["Category"] = relationship("Category", back_populates="tickets")
    location: Mapped["Location"] = relationship(
        "Location",
        back_populates="ticket",
        cascade="all, delete-orphan",
        single_parent=True,
    )
    reporter: Mapped["User"] = relationship(
        "User",
        foreign_keys=[reporter_id],
        back_populates="reported_tickets",
    )
    assigned_team: Mapped["Team | None"] = relationship(
        "Team",
        foreign_keys=[team_id],
        back_populates="assigned_tickets",
    )
    photos: Mapped[list["Photo"]] = relationship(
        "Photo", back_populates="ticket", cascade="all, delete-orphan"
    )
    comments: Mapped[list["Comment"]] = relationship(
        "Comment", back_populates="ticket", cascade="all, delete-orphan"
    )
    followers: Mapped[list["TicketFollower"]] = relationship(
        "TicketFollower", back_populates="ticket", cascade="all, delete-orphan"
    )
    status_logs: Mapped[list["StatusLog"]] = relationship(
        "StatusLog", back_populates="ticket", cascade="all, delete-orphan"
    )
    feedback: Mapped["Feedback | None"] = relationship(
        "Feedback", back_populates="ticket", uselist=False
    )
    escalations: Mapped[list["EscalationRequest"]] = relationship(
        "EscalationRequest",
        back_populates="ticket",
        order_by="EscalationRequest.created_at.desc()",
    )

    @property
    def active_escalation(self) -> "EscalationRequest | None":
        """Return the pending escalation if one exists."""
        from app.models.escalation import EscalationStatus
        for esc in self.escalations:
            if esc.status == EscalationStatus.PENDING:
                return esc
        return None

    @property
    def latest_escalation(self) -> "EscalationRequest | None":
        """Return the most recent escalation."""
        return self.escalations[0] if self.escalations else None

    def __repr__(self) -> str:
        return f"<Ticket {self.id} ({self.status.value})>"


class TicketFollower(Base):
    """Junction table for users following tickets."""

    __tablename__ = "ticket_followers"

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tickets.id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    followed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="followers")
    user: Mapped["User"] = relationship("User")


class StatusLog(Base, UUIDMixin):
    """Log of ticket status changes."""

    __tablename__ = "status_logs"

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
    )
    old_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    new_status: Mapped[str] = mapped_column(String(50), nullable=False)
    changed_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="status_logs")
    changed_by: Mapped["User | None"] = relationship("User")


# Forward references
from app.models.category import Category  # noqa: E402, F401
from app.models.user import User  # noqa: E402, F401
from app.models.team import Team  # noqa: E402, F401
from app.models.photo import Photo  # noqa: E402, F401
from app.models.comment import Comment  # noqa: E402, F401
from app.models.feedback import Feedback  # noqa: E402, F401
from app.models.escalation import EscalationRequest  # noqa: E402, F401
