"""District model for location management."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class District(Base, UUIDMixin, TimestampMixin):
    """District model representing city districts."""

    __tablename__ = "districts"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationships
    team_assignments: Mapped[list["TeamDistrict"]] = relationship(
        "TeamDistrict", back_populates="district", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<District {self.name}, {self.city}>"

    __table_args__ = (
        {"comment": "City districts for team assignment and location mapping"},
    )


# Forward reference
from app.models.team import TeamDistrict  # noqa: E402, F401

