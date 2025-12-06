"""Saved address schemas."""

from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema, TimestampSchema


class SavedAddressBase(BaseSchema):
    """Base saved address schema."""

    name: str = Field(..., min_length=1, max_length=100)
    address: str = Field(..., min_length=1, max_length=500)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    city: str | None = Field(default="Istanbul", max_length=100)


class SavedAddressCreate(SavedAddressBase):
    """Schema for creating a saved address."""

    pass


class SavedAddressUpdate(BaseSchema):
    """Schema for updating a saved address."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    address: str | None = Field(default=None, min_length=1, max_length=500)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    city: str | None = Field(default=None, max_length=100)


class SavedAddressResponse(SavedAddressBase, TimestampSchema):
    """Saved address response schema."""

    id: UUID
    user_id: UUID


class SavedAddressListResponse(BaseSchema):
    """Response for listing saved addresses."""

    items: list[SavedAddressResponse]
    total: int

