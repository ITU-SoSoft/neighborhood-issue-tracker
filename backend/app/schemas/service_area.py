"""Service Area schemas."""

from uuid import UUID

from app.schemas.base import BaseSchema, TimestampSchema


class ServiceAreaCreate(BaseSchema):
    """Schema for creating a service area."""

    team_id: UUID
    category_id: UUID
    district_id: UUID


class ServiceAreaResponse(TimestampSchema):
    """Service area response schema."""

    id: UUID
    team_id: UUID
    team_name: str | None = None
    category_id: UUID
    category_name: str | None = None
    district_id: UUID
    district_name: str | None = None


class ServiceAreaListResponse(BaseSchema):
    """Response for listing service areas."""

    items: list[ServiceAreaResponse]
    total: int

