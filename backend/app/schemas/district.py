"""District schemas."""

from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema, TimestampSchema


class DistrictCreate(BaseSchema):
    """Schema for creating a district."""

    name: str = Field(..., min_length=2, max_length=100)
    city: str = Field(default="Istanbul", max_length=100)


class DistrictUpdate(BaseSchema):
    """Schema for updating a district."""

    name: str | None = Field(default=None, min_length=2, max_length=100)
    city: str | None = Field(default=None, max_length=100)


class DistrictResponse(TimestampSchema):
    """District response schema."""

    id: UUID
    name: str
    city: str


class DistrictListResponse(BaseSchema):
    """Response for listing districts."""

    items: list[DistrictResponse]
    total: int

