"""Saved address model for users."""

import uuid

from sqlalchemy import ForeignKey, String, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class SavedAddress(Base, UUIDMixin, TimestampMixin):
    """Saved address model for user's favorite locations."""

    __tablename__ = "saved_addresses"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "Home", "Work"
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=True, default="Istanbul")

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="saved_addresses")

    def __repr__(self) -> str:
        return f"<SavedAddress {self.name}: {self.address[:30]}...>"


# Forward reference
from app.models.user import User  # noqa: E402

