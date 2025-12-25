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


async def notify_comment_added(
    db: AsyncSession,
    ticket: Ticket,
    comment_author: User,
    comment_text: str,
) -> None:
    """Notify ticket reporter, followers, and team members when a comment is added."""
    # Truncate comment for notification message
    preview = comment_text[:50] + "..." if len(comment_text) > 50 else comment_text
    
    # Track who we've already notified to avoid duplicates
    notified_user_ids = set()
    
    # Notify reporter (if not the comment author)
    if ticket.reporter_id != comment_author.id:
        await create_notification(
            db=db,
            user_id=ticket.reporter_id,
            notification_type=NotificationType.COMMENT_ADDED,
            title="New Comment",
            message=f'{comment_author.name} commented on your ticket: "{preview}"',
            ticket_id=ticket.id,
        )
        notified_user_ids.add(ticket.reporter_id)
    
    # Notify followers (except reporter and comment author)
    query = select(TicketFollower).where(
        TicketFollower.ticket_id == ticket.id,
        TicketFollower.user_id != ticket.reporter_id,
        TicketFollower.user_id != comment_author.id,
    )
    result = await db.execute(query)
    followers = result.scalars().all()
    
    for follower in followers:
        await create_notification(
            db=db,
            user_id=follower.user_id,
            notification_type=NotificationType.COMMENT_ADDED,
            title="New Comment",
            message=f'{comment_author.name} commented on ticket "{ticket.title}": "{preview}"',
            ticket_id=ticket.id,
        )
        notified_user_ids.add(follower.user_id)
    
    # Notify team members (if ticket is assigned to a team)
    if ticket.team_id:
        from app.models.user import UserRole
        
        # Get team members with SUPPORT role (users with this team_id)
        team_query = select(User).where(
            User.team_id == ticket.team_id,
            User.role == UserRole.SUPPORT
        )
        team_result = await db.execute(team_query)
        team_members = team_result.scalars().all()
        
        # Notify each team member (if not already notified and not the comment author)
        for member in team_members:
            if member.id not in notified_user_ids and member.id != comment_author.id:
                await create_notification(
                    db=db,
                    user_id=member.id,
                    notification_type=NotificationType.COMMENT_ADDED,
                    title="New Comment on Team Ticket",
                    message=f'{comment_author.name} commented on ticket "{ticket.title}": "{preview}"',
                    ticket_id=ticket.id,
                )
                notified_user_ids.add(member.id)


async def notify_ticket_assigned(
    db: AsyncSession,
    ticket: Ticket,
) -> None:
    """Notify team members when a ticket is assigned to their team."""
    if not ticket.team_id:
        return
    
    # Get team members (users with this team_id)
    from app.models.user import UserRole
    
    query = select(User).where(
        User.team_id == ticket.team_id,
        User.role == UserRole.SUPPORT
    )
    result = await db.execute(query)
    team_members = result.scalars().all()
    
    # Notify each team member
    for member in team_members:
        # Don't notify if they're the reporter
        if member.id == ticket.reporter_id:
            continue
            
        await create_notification(
            db=db,
            user_id=member.id,
            notification_type=NotificationType.TICKET_ASSIGNED,
            title="Ticket Assigned to Your Team",
            message=f'New ticket "{ticket.title}" has been assigned to your team.',
            ticket_id=ticket.id,
        )


async def notify_new_ticket_for_team(
    db: AsyncSession,
    ticket: Ticket,
) -> None:
    """Notify support team members when a new ticket is created for their team."""
    if not ticket.team_id:
        return
    
    # Get team members with SUPPORT role (users with this team_id)
    from app.models.user import UserRole
    
    query = select(User).where(
        User.team_id == ticket.team_id,
        User.role == UserRole.SUPPORT
    )
    result = await db.execute(query)
    team_members = result.scalars().all()
    
    # Notify each support team member
    for member in team_members:
        await create_notification(
            db=db,
            user_id=member.id,
            notification_type=NotificationType.NEW_TICKET_FOR_TEAM,
            title="New Ticket for Your Team",
            message=f'New ticket "{ticket.title}" has been created in your team\'s district.',
            ticket_id=ticket.id,
        )


async def notify_escalation_requested(
    db: AsyncSession,
    ticket: Ticket,
    escalation_reason: str,
    requester: User,
) -> None:
    """Notify managers when an escalation is requested."""
    from app.models.user import UserRole
    
    # Get all managers
    query = select(User).where(User.role == UserRole.MANAGER)
    result = await db.execute(query)
    managers = result.scalars().all()
    
    reason_preview = escalation_reason[:50] + "..." if len(escalation_reason) > 50 else escalation_reason
    
    # Notify each manager
    for manager in managers:
        await create_notification(
            db=db,
            user_id=manager.id,
            notification_type=NotificationType.ESCALATION_REQUESTED,
            title="Escalation Request",
            message=f'{requester.name} requested escalation for ticket "{ticket.title}": {reason_preview}',
            ticket_id=ticket.id,
        )


async def notify_escalation_decision(
    db: AsyncSession,
    ticket: Ticket,
    approved: bool,
    decided_by: User,
) -> None:
    """Notify ticket reporter and requester when escalation is approved/rejected."""
    notification_type = (
        NotificationType.ESCALATION_APPROVED if approved 
        else NotificationType.ESCALATION_REJECTED
    )
    title = "Escalation Approved" if approved else "Escalation Rejected"
    action = "approved" if approved else "rejected"
    
    # Notify reporter
    await create_notification(
        db=db,
        user_id=ticket.reporter_id,
        notification_type=notification_type,
        title=title,
        message=f'Your ticket "{ticket.title}" escalation request has been {action}.',
        ticket_id=ticket.id,
    )

