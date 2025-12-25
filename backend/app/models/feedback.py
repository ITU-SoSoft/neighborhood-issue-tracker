"""Feedback model for citizen ratings."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import UUIDMixin


class Feedback(Base, UUIDMixin):
    """Feedback model for citizen ratings after ticket resolution."""

    __tablename__ = "feedbacks"

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tickets.id", ondelete="CASCADE"),
        unique=True,  # One feedback per ticket
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    rating: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )  # 1-5 stars
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.now(),
    )

    # Relationships
    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="feedback")
    user: Mapped["User | None"] = relationship("User", back_populates="feedbacks")

    def __repr__(self) -> str:
        return f"<Feedback {self.rating}/5 for Ticket {self.ticket_id}>"


# Forward references
from app.models.ticket import Ticket  # noqa: E402, F401
from app.models.user import User  # noqa: E402, F401
