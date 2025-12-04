"""Team schemas for request/response validation."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TeamBase(BaseModel):
    """Base schema for team data."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)


class TeamCreate(TeamBase):
    """Schema for creating a team."""

    pass


class TeamUpdate(BaseModel):
    """Schema for updating a team."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)


class TeamResponse(TeamBase):
    """Schema for team response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class TeamListResponse(BaseModel):
    """Schema for team list response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    member_count: int = 0


class TeamMemberResponse(BaseModel):
    """Schema for team member in team response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    phone_number: str
    role: str


class TeamDetailResponse(TeamResponse):
    """Schema for detailed team response with members."""

    members: list[TeamMemberResponse] = []
