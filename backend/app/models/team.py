"""Team model for organizing support staff."""

from sqlalchemy import String, Text
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
    service_areas: Mapped[list["ServiceArea"]] = relationship(
        "ServiceArea", back_populates="team", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Team {self.name}>"


# Forward references
from app.models.service_area import ServiceArea  # noqa: E402, F401
from app.models.user import User  # noqa: E402, F401
