"""Category model for ticket categorization."""

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class Category(Base, UUIDMixin, TimestampMixin):
    """Category model for classifying tickets."""

    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    tickets: Mapped[list["Ticket"]] = relationship("Ticket", back_populates="category")

    def __repr__(self) -> str:
        return f"<Category {self.name}>"


# Forward reference
from app.models.ticket import Ticket  # noqa: E402, F401
