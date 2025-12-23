"""Notification service for creating notifications."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.notification import Notification, NotificationType
from app.models.ticket import Ticket, TicketStatus, TicketFollower
from app.models.user import User


async def create_notification(
    db: AsyncSession,
    user_id: UUID,
    notification_type: NotificationType,
    title: str,
    message: str,
    ticket_id: UUID | None = None,
) -> Notification:
    """Create a new notification."""
    notification = Notification(
        user_id=user_id,
        ticket_id=ticket_id,
        notification_type=notification_type,
        title=title,
        message=message,
        is_read=False,
    )
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    return notification


async def notify_ticket_created(
    db: AsyncSession,
    ticket: Ticket,
) -> None:
    """Notify user when they create a ticket."""
    await create_notification(
        db=db,
        user_id=ticket.reporter_id,
        notification_type=NotificationType.TICKET_CREATED,
        title="Ticket Created",
        message=f'Your ticket "{ticket.title}" has been created successfully.',
        ticket_id=ticket.id,
    )


async def notify_ticket_followed(
    db: AsyncSession,
    ticket: Ticket,
    follower: User,
) -> None:
    """Notify ticket reporter when someone follows their ticket."""
    # Don't notify if user follows own ticket
    if ticket.reporter_id != follower.id:
        await create_notification(
            db=db,
            user_id=ticket.reporter_id,
            notification_type=NotificationType.TICKET_FOLLOWED,
            title="New Follower",
            message=f'{follower.name} started following your ticket "{ticket.title}".',
            ticket_id=ticket.id,
        )


async def notify_ticket_status_changed(
    db: AsyncSession,
    ticket: Ticket,
    old_status: TicketStatus,
    new_status: TicketStatus,
    changed_by: User,
) -> None:
    """Notify ticket reporter and followers when status changes."""
    status_labels = {
        TicketStatus.NEW: "New",
        TicketStatus.IN_PROGRESS: "In Progress",
        TicketStatus.RESOLVED: "Resolved",
        TicketStatus.CLOSED: "Closed",
        TicketStatus.ESCALATED: "Escalated",
    }
    
    old_label = status_labels.get(old_status, old_status.value)
    new_label = status_labels.get(new_status, new_status.value)
    
    # Notify reporter (if not the one who changed it)
    if ticket.reporter_id != changed_by.id:
        await create_notification(
            db=db,
            user_id=ticket.reporter_id,
            notification_type=NotificationType.TICKET_STATUS_CHANGED,
            title="Status Updated",
            message=f'Your ticket "{ticket.title}" status changed from {old_label} to {new_label}.',
            ticket_id=ticket.id,
        )
    
    # Notify followers (except reporter and the one who changed it)
    query = select(TicketFollower).where(
        TicketFollower.ticket_id == ticket.id,
        TicketFollower.user_id != ticket.reporter_id,
        TicketFollower.user_id != changed_by.id,
    )
    result = await db.execute(query)
    followers = result.scalars().all()
    
    for follower in followers:
        await create_notification(
            db=db,
            user_id=follower.user_id,
            notification_type=NotificationType.TICKET_STATUS_CHANGED,
            title="Ticket Updated",
            message=f'Ticket "{ticket.title}" status changed from {old_label} to {new_label}.',
            ticket_id=ticket.id,
        )

