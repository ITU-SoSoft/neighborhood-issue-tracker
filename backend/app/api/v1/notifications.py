"""Notification endpoints."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DatabaseSession
from app.models.notification import Notification
from app.schemas.notification import (
    NotificationListResponse,
    NotificationResponse,
)

router = APIRouter()


@router.get(
    "",
    response_model=NotificationListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_notifications(
    current_user: CurrentUser,
    db: DatabaseSession,
    unread_only: bool = Query(default=False),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> NotificationListResponse:
    """List notifications for the current user."""
    query = select(Notification).where(Notification.user_id == current_user.id)

    if unread_only:
        query = query.where(Notification.is_read == False)  # noqa: E712

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Get paginated results
    query = (
        query.options(selectinload(Notification.ticket))
        .order_by(Notification.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    result = await db.execute(query)
    notifications = result.unique().scalars().all()

    return NotificationListResponse(
        items=[NotificationResponse.model_validate(n) for n in notifications],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/unread-count",
    response_model=dict,
    status_code=status.HTTP_200_OK,
)
async def get_unread_count(
    current_user: CurrentUser,
    db: DatabaseSession,
) -> dict:
    """Get count of unread notifications."""
    query = select(func.count()).where(
        Notification.user_id == current_user.id,
        Notification.is_read == False,  # noqa: E712
    )
    count = (await db.execute(query)).scalar() or 0
    return {"count": count}


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    status_code=status.HTTP_200_OK,
)
async def mark_as_read(
    notification_id: UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> NotificationResponse:
    """Mark a notification as read."""
    query = select(Notification).where(
        Notification.id == notification_id,
        Notification.user_id == current_user.id,
    )
    result = await db.execute(query)
    notification = result.scalar_one_or_none()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
        )

    notification.is_read = True
    notification.read_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(notification)

    return NotificationResponse.model_validate(notification)


@router.patch(
    "/read-all",
    status_code=status.HTTP_200_OK,
)
async def mark_all_as_read(
    current_user: CurrentUser,
    db: DatabaseSession,
) -> dict:
    """Mark all notifications as read."""
    query = select(Notification).where(
        Notification.user_id == current_user.id,
        Notification.is_read == False,  # noqa: E712
    )
    result = await db.execute(query)
    notifications = result.scalars().all()

    now = datetime.now(timezone.utc)
    for notification in notifications:
        notification.is_read = True
        notification.read_at = now

    await db.commit()

    return {"message": "All notifications marked as read"}

