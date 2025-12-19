"""Team schemas."""

from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema, TimestampSchema


class TeamCreate(BaseSchema):
    """Schema for creating a team."""

    name: str = Field(..., min_length=3, max_length=100)
    description: str | None = Field(default=None, max_length=500)


class TeamUpdate(BaseSchema):
    """Schema for updating a team."""

    name: str | None = Field(default=None, min_length=3, max_length=100)
    description: str | None = Field(default=None, max_length=500)


class TeamResponse(TimestampSchema):
    """Team response schema."""

    id: UUID
    name: str
    description: str | None
    member_count: int = 0
    active_ticket_count: int = 0


class TeamDistrictCreate(BaseSchema):
    """Schema for assigning district to team."""

    district_id: UUID


class TeamDistrictResponse(BaseSchema):
    """Team district response schema."""

    team_id: UUID
    district_id: UUID
    district_name: str
    city: str


class TeamCategoryCreate(BaseSchema):
    """Schema for assigning category to team."""

    category_id: UUID


class TeamCategoryResponse(BaseSchema):
    """Team category response schema."""

    team_id: UUID
    category_id: UUID
    category_name: str


class TeamDetailResponse(TeamResponse):
    """Detailed team response with assignments."""

    districts: list[TeamDistrictResponse] = []
    categories: list[TeamCategoryResponse] = []


class TeamMemberResponse(BaseSchema):
    """Team member response schema."""

    id: UUID
    name: str
    email: str
    role: str


class TeamListResponse(BaseSchema):
    """Response for listing teams."""

    items: list[TeamResponse]
    total: int
    page: int = 1
    page_size: int = 20
