"""Comment schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema


class CommentCreate(BaseSchema):
    """Schema for creating a comment."""

    content: str = Field(..., min_length=1, max_length=2000)
    is_internal: bool = Field(
        default=False,
        description="If true, comment is hidden from citizens",
    )


class CommentResponse(BaseSchema):
    """Comment response schema."""

    id: UUID
    ticket_id: UUID
    user_id: UUID | None
    user_name: str | None = None
    content: str
    is_internal: bool
    created_at: datetime


class CommentListResponse(BaseSchema):
    """Response for listing comments."""

    items: list[CommentResponse]
    total: int
