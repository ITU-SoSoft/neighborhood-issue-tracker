"""District schemas."""

from uuid import UUID

from app.schemas.base import BaseSchema, TimestampSchema


class DistrictResponse(TimestampSchema):
    """District response schema."""

    id: UUID
    name: str
    city: str


class DistrictListResponse(BaseSchema):
    """Response for listing districts."""

    items: list[DistrictResponse]
    total: int
