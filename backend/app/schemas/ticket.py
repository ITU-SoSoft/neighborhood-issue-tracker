"""Ticket schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import Field, field_validator

from app.models.ticket import TicketStatus
from app.schemas.base import BaseSchema, TimestampSchema


class LocationCreate(BaseSchema):
    """Schema for creating a location.
    
    Either provide GPS coordinates (latitude/longitude) OR district_id.
    """

    latitude: float | None = Field(default=None, ge=-90, le=90, description="Latitude coordinate")
    longitude: float | None = Field(default=None, ge=-180, le=180, description="Longitude coordinate")
    address: str | None = Field(default=None, max_length=500)
    district_id: UUID | None = Field(default=None, description="District ID for location")
    city: str = Field(default="Istanbul", max_length=100)
    
    @field_validator("district_id")
    @classmethod
    def validate_location(cls, v, info):
        """Validate that either GPS coordinates or district_id is provided."""
        data = info.data
        has_gps = data.get("latitude") is not None and data.get("longitude") is not None
        has_district = v is not None
        
        if not has_gps and not has_district:
            raise ValueError("Either provide GPS coordinates (latitude & longitude) or district_id")
        
        return v


class LocationResponse(BaseSchema):
    """Location response schema."""

    id: UUID
    latitude: float
    longitude: float
    address: str | None
    district: str | None
    city: str


class TicketCreate(BaseSchema):
    """Schema for creating a new ticket."""

    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10, max_length=5000)
    category_id: UUID
    location: LocationCreate

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Clean and validate title."""
        return " ".join(v.split())


class TicketUpdate(BaseSchema):
    """Schema for updating a ticket."""

    title: str | None = Field(default=None, min_length=5, max_length=200)
    description: str | None = Field(default=None, min_length=10, max_length=5000)
    category_id: UUID | None = None


class TicketStatusUpdate(BaseSchema):
    """Schema for updating ticket status."""

    status: TicketStatus
    comment: str | None = Field(default=None, max_length=1000)


class TicketAssignUpdate(BaseSchema):
    """Schema for assigning a ticket to a team."""

    team_id: UUID


class TicketResponse(TimestampSchema):
    """Ticket response schema."""

    id: UUID
    title: str
    description: str
    status: TicketStatus
    category_id: UUID
    category_name: str | None = None
    location: LocationResponse
    reporter_id: UUID
    reporter_name: str | None = None
    team_id: UUID | None = None
    team_name: str | None = None
    resolved_at: datetime | None = None
    photo_count: int = 0
    comment_count: int = 0
    follower_count: int = 0


class TicketListResponse(BaseSchema):
    """Response for listing tickets."""

    items: list[TicketResponse]
    total: int
    page: int
    page_size: int


class TicketDetailResponse(TicketResponse):
    """Detailed ticket response with related data."""

    photos: list["PhotoResponse"] = []
    comments: list["CommentResponse"] = []
    has_feedback: bool = False
    has_escalation: bool = False
    is_following: bool = False


class NearbyTicketResponse(BaseSchema):
    """Response for nearby tickets."""

    id: UUID
    title: str
    status: TicketStatus
    category_name: str
    distance_meters: float
    follower_count: int


# Forward references
from app.schemas.comment import CommentResponse  # noqa: E402
from app.schemas.photo import PhotoResponse  # noqa: E402

TicketDetailResponse.model_rebuild()
