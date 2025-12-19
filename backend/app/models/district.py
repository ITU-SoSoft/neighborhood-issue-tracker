"""District model for geographic regions."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class District(Base, UUIDMixin, TimestampMixin):
    """District model representing geographic regions (ilçe)."""

    __tablename__ = "districts"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    # Optional: Add coordinates for district center if needed later
    # latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    # longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    service_areas: Mapped[list["ServiceArea"]] = relationship(
        "ServiceArea", back_populates="district"
    )

    def __repr__(self) -> str:
        return f"<District {self.name}>"


# Forward reference
from app.models.service_area import ServiceArea  # noqa: E402, F401

