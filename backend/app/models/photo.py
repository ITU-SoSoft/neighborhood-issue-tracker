"""Photo model for ticket images."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import UUIDMixin


class PhotoType(str, enum.Enum):
    """Photo type enumeration."""

    REPORT = "REPORT"  # Uploaded by citizen when reporting
    PROOF = "PROOF"  # Uploaded by support as proof of resolution


class Photo(Base, UUIDMixin):
    """Photo model for ticket images stored in MinIO."""

    __tablename__ = "photos"

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
    )
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    photo_type: Mapped[PhotoType] = mapped_column(
        Enum(PhotoType),
        default=PhotoType.REPORT,
        nullable=False,
    )
    uploaded_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="photos")
    uploaded_by: Mapped["User | None"] = relationship("User")

    def __repr__(self) -> str:
        return f"<Photo {self.filename} ({self.photo_type.value})>"


# Forward references
from app.models.ticket import Ticket  # noqa: E402, F401
from app.models.user import User  # noqa: E402, F401
