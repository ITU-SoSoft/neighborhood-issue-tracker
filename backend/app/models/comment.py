"""Comment model for ticket discussions."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import UUIDMixin


class Comment(Base, UUIDMixin):
    """Comment model for ticket discussions."""

    __tablename__ = "comments"

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_internal: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )  # True = hidden from citizen
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="comments")
    user: Mapped["User | None"] = relationship("User", back_populates="comments")

    def __repr__(self) -> str:
        return f"<Comment {self.id} on Ticket {self.ticket_id}>"


# Forward references
from app.models.ticket import Ticket  # noqa: E402, F401
from app.models.user import User  # noqa: E402, F401
