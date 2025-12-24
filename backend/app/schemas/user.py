"""User schemas."""

import re
from datetime import datetime
from uuid import UUID

from pydantic import Field, field_validator

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


class UserCreateRequest(BaseSchema):
    """Schema for creating a new user (manager only)."""

    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="User's full name",
    )
    email: str = Field(
        ...,
        description="Email address",
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="User password (min 8 chars)",
    )
    phone_number: str = Field(
        ...,
        description="Turkish phone number in format +90XXXXXXXXXX",
        pattern=r"^\+90[0-9]{10}$",
    )
    role: UserRole = Field(
        default=UserRole.SUPPORT,
        description="User role (default: SUPPORT)",
    )
    team_id: UUID | None = Field(
        default=None,
        description="Team ID (optional)",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate and clean name."""
        cleaned = " ".join(v.split())  # Normalize whitespace
        if len(cleaned) < 2:
            raise ValueError("Name must be at least 2 characters")
        return cleaned

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate and normalize email address."""
        from email_validator import EmailNotValidError, validate_email

        try:
            validated = validate_email(v, check_deliverability=False)
            return validated.normalized
        except EmailNotValidError as e:
            raise ValueError(str(e))

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password meets complexity requirements."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserUpdate(BaseSchema):
    """Schema for updating user profile."""

    name: str | None = Field(default=None, min_length=2, max_length=100)
    email: str | None = None
    phone_number: str | None = Field(default=None, pattern=r"^\+90[0-9]{10}$")
    current_password: str | None = Field(
        default=None,
        min_length=8,
        max_length=128,
        description="Current password (required when changing password)",
    )
    new_password: str | None = Field(
        default=None,
        min_length=8,
        max_length=128,
        description="New password (min 8 chars)",
    )


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
