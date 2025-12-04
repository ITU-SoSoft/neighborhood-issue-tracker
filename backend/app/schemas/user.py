"""User schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.models.user import UserRole
from app.schemas.base import BaseSchema, TimestampSchema


class UserBase(BaseSchema):
    """Base user schema."""

    phone_number: str
    name: str
    email: str | None = None
    role: UserRole


class UserCreate(BaseSchema):
    """Schema for creating a user (internal use)."""

    phone_number: str
    name: str = "New User"
    email: str | None = None
    role: UserRole = UserRole.CITIZEN


class UserUpdate(BaseSchema):
    """Schema for updating user profile."""

    name: str | None = Field(default=None, min_length=2, max_length=100)
    email: str | None = None


class UserRoleUpdate(BaseSchema):
    """Schema for updating user role (manager only)."""

    role: UserRole
    team_id: UUID | None = None


class UserResponse(UserBase, TimestampSchema):
    """User response schema."""

    id: UUID
    is_verified: bool
    is_active: bool
    team_id: UUID | None = None


class UserListResponse(BaseSchema):
    """Response for listing users."""

    items: list[UserResponse]
    total: int
    page: int = 1
    page_size: int = 20


class CurrentUserResponse(UserResponse):
    """Response for current authenticated user."""

    pass
