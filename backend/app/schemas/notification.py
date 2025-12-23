"""Notification schemas."""

from datetime import datetime
from uuid import UUID


from app.models.notification import NotificationType
from app.schemas.base import BaseSchema, TimestampSchema


class NotificationResponse(TimestampSchema):
    """Notification response schema."""

    id: UUID
    user_id: UUID
    ticket_id: UUID | None
    notification_type: NotificationType
    title: str
    message: str
    is_read: bool
    read_at: datetime | None


class NotificationListResponse(BaseSchema):
    """Paginated notification list response."""

    items: list[NotificationResponse]
    total: int
    page: int
    page_size: int

