"""Escalation model for manager approval workflow."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import UUIDMixin


class EscalationStatus(str, enum.Enum):
    """Escalation status enumeration."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class EscalationRequest(Base, UUIDMixin):
    """Escalation request model for manager approval workflow."""

    __tablename__ = "escalation_requests"

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tickets.id", ondelete="CASCADE"),
        unique=True,  # One escalation per ticket
        nullable=False,
    )
    requester_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )  # Support member who escalated
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )  # Manager who reviewed
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[EscalationStatus] = mapped_column(
        Enum(EscalationStatus),
        default=EscalationStatus.PENDING,
        nullable=False,
    )
    review_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="escalation")
    requester: Mapped["User | None"] = relationship("User", foreign_keys=[requester_id])
    reviewer: Mapped["User | None"] = relationship("User", foreign_keys=[reviewer_id])

    def __repr__(self) -> str:
        return f"<EscalationRequest {self.id} ({self.status.value})>"


# Forward references
from app.models.ticket import Ticket  # noqa: E402, F401
from app.models.user import User  # noqa: E402, F401
