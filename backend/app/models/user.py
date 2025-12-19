"""User and OTP models."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin, UUIDMixin


class UserRole(str, enum.Enum):
    """User role enumeration."""

    CITIZEN = "CITIZEN"
    SUPPORT = "SUPPORT"
    MANAGER = "MANAGER"


class User(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """User model representing all system users."""

    __tablename__ = "users"

    # Phone number is the primary identifier (Turkish format: +90XXXXXXXXXX)
    phone_number: Mapped[str] = mapped_column(
        String(15),
        unique=True,
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole),
        default=UserRole.CITIZEN,
        nullable=False,
    )

    # Team association (for support/manager roles)
    team_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="SET NULL"),
        nullable=True,
    )

    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    team: Mapped["Team | None"] = relationship("Team", back_populates="members")
    reported_tickets: Mapped[list["Ticket"]] = relationship(
        "Ticket",
        foreign_keys="Ticket.reporter_id",
        back_populates="reporter",
    )
    assigned_tickets: Mapped[list["Ticket"]] = relationship(
        "Ticket",
        foreign_keys="Ticket.assignee_id",
        back_populates="assignee",
    )
    comments: Mapped[list["Comment"]] = relationship("Comment", back_populates="user")
    feedbacks: Mapped[list["Feedback"]] = relationship(
        "Feedback", back_populates="user"
    )
    saved_addresses: Mapped[list["SavedAddress"]] = relationship(
        "SavedAddress", back_populates="user", cascade="all, delete-orphan"
    )
    notifications: Mapped[list["Notification"]] = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.phone_number} ({self.role.value})>"


class OTPCode(Base, UUIDMixin):
    """OTP code model for phone verification."""

    __tablename__ = "otp_codes"

    phone_number: Mapped[str] = mapped_column(
        String(15),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(6), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<OTPCode {self.phone_number}>"

    @property
    def is_expired(self) -> bool:
        """Check if the OTP code has expired."""
        return datetime.now(self.expires_at.tzinfo) > self.expires_at


# Forward references for type hints
from app.models.team import Team  # noqa: E402
from app.models.ticket import Ticket  # noqa: E402
from app.models.comment import Comment  # noqa: E402
from app.models.feedback import Feedback  # noqa: E402
from app.models.address import SavedAddress  # noqa: E402
from app.models.notification import Notification  # noqa: E402
