"""Photo schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.models.photo import PhotoType
from app.schemas.base import BaseSchema


class PhotoCreate(BaseSchema):
    """Schema for creating a photo record."""

    filename: str
    url: str
    photo_type: PhotoType = PhotoType.REPORT


class PhotoResponse(BaseSchema):
    """Photo response schema."""

    id: UUID
    url: str
    filename: str
    photo_type: PhotoType
    uploaded_by_id: UUID | None
    uploaded_at: datetime


class PhotoUploadResponse(BaseSchema):
    """Response after uploading a photo."""

    id: UUID
    url: str
    filename: str
    message: str = "Photo uploaded successfully"
