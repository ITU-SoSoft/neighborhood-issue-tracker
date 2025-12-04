"""Category schemas."""

from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema, TimestampSchema


class CategoryCreate(BaseSchema):
    """Schema for creating a category."""

    name: str = Field(..., min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=500)


class CategoryUpdate(BaseSchema):
    """Schema for updating a category."""

    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class CategoryResponse(TimestampSchema):
    """Category response schema."""

    id: UUID
    name: str
    description: str | None
    is_active: bool


class CategoryListResponse(BaseSchema):
    """Response for listing categories."""

    items: list[CategoryResponse]
    total: int
