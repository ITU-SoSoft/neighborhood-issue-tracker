"""Feedback schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema


class FeedbackCreate(BaseSchema):
    """Schema for creating feedback."""

    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars")
    comment: str | None = Field(default=None, max_length=1000)

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v: int) -> int:
        """Ensure rating is between 1 and 5."""
        if not 1 <= v <= 5:
            raise ValueError("Rating must be between 1 and 5")
        return v


class FeedbackUpdate(BaseSchema):
    """Schema for updating feedback."""

    rating: int | None = Field(default=None, ge=1, le=5, description="Rating from 1 to 5 stars")
    comment: str | None = Field(default=None, max_length=1000)

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v: int | None) -> int | None:
        """Ensure rating is between 1 and 5 if provided."""
        if v is not None and not 1 <= v <= 5:
            raise ValueError("Rating must be between 1 and 5")
        return v


class FeedbackResponse(BaseSchema):
    """Feedback response schema."""

    id: UUID
    ticket_id: UUID
    user_id: UUID | None
    user_name: str | None = None
    rating: int
    comment: str | None
    created_at: datetime
    updated_at: datetime | None = None
