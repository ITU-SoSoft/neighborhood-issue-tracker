"""Service Area model for team assignments by district and category."""

import uuid

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class ServiceArea(Base, UUIDMixin, TimestampMixin):
    """Service Area model mapping teams to district+category combinations.
    
    This allows flexible assignment where:
    - A team can handle multiple district+category combinations
    - A district+category can have multiple teams (for load balancing)
    """

    __tablename__ = "service_areas"

    # Foreign keys
    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
    )
    district_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("districts.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationships
    team: Mapped["Team"] = relationship("Team", back_populates="service_areas")
    category: Mapped["Category"] = relationship("Category", back_populates="service_areas")
    district: Mapped["District"] = relationship("District", back_populates="service_areas")

    # Ensure unique combination (optional: remove if multiple teams can serve same area)
    __table_args__ = (
        UniqueConstraint(
            "team_id",
            "category_id",
            "district_id",
            name="uq_service_area_team_category_district",
        ),
    )

    def __repr__(self) -> str:
        return f"<ServiceArea team={self.team_id} cat={self.category_id} dist={self.district_id}>"


# Forward references
from app.models.category import Category  # noqa: E402, F401
from app.models.district import District  # noqa: E402, F401
from app.models.team import Team  # noqa: E402, F401

