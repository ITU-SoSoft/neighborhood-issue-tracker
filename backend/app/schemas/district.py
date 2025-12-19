"""District schemas."""

from uuid import UUID

from app.schemas.base import BaseSchema, TimestampSchema


class DistrictCreate(BaseSchema):
    """Schema for creating a district."""

    name: str


class DistrictUpdate(BaseSchema):
    """Schema for updating a district."""

    name: str | None = None


class DistrictResponse(TimestampSchema):
    """District response schema."""

    id: UUID
    name: str


class DistrictListResponse(BaseSchema):
    """Response for listing districts."""

    items: list[DistrictResponse]
    total: int

