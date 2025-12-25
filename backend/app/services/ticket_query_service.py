"""Ticket query service for shared queries and response builders."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models.comment import Comment
from app.models.escalation import EscalationStatus
from app.models.ticket import StatusLog, Ticket, TicketStatus
from app.models.user import User, UserRole
from app.schemas.comment import CommentResponse
from app.schemas.ticket import StatusLogResponse, TicketDetailResponse, TicketResponse


# Valid status transitions - business rule
VALID_TRANSITIONS = {
    TicketStatus.NEW: [TicketStatus.IN_PROGRESS, TicketStatus.ESCALATED],
    TicketStatus.IN_PROGRESS: [TicketStatus.RESOLVED, TicketStatus.ESCALATED],
    TicketStatus.ESCALATED: [TicketStatus.IN_PROGRESS],
    TicketStatus.RESOLVED: [TicketStatus.CLOSED, TicketStatus.IN_PROGRESS],
    TicketStatus.CLOSED: [TicketStatus.IN_PROGRESS],  # Allow going back to IN_PROGRESS
}


def build_ticket_response(ticket: Ticket, current_user: User) -> TicketResponse:
    """Build a ticket response with computed fields.

    Args:
        ticket: The ticket model with loaded relationships.
        current_user: The current authenticated user.

    Returns:
        TicketResponse schema with computed fields.
    """
    return TicketResponse(
        id=ticket.id,
        title=ticket.title,
        description=ticket.description,
        status=ticket.status,
        category_id=ticket.category_id,
        category_name=ticket.category.name if ticket.category else None,
        location=ticket.location,
        reporter_id=ticket.reporter_id,
        reporter_name=ticket.reporter.name if ticket.reporter else None,
        team_id=ticket.team_id,
        team_name=ticket.assigned_team.name if ticket.assigned_team else None,
        resolved_at=ticket.resolved_at,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        photo_count=len(ticket.photos) if ticket.photos else 0,
        comment_count=len(ticket.comments) if ticket.comments else 0,
        follower_count=len(ticket.followers) if ticket.followers else 0,
    )


def build_ticket_detail_response(
    ticket: Ticket, current_user: User
) -> TicketDetailResponse:
    """Build a detailed ticket response with related data.

    Args:
        ticket: The ticket model with loaded relationships.
        current_user: The current authenticated user.

    Returns:
        TicketDetailResponse schema with photos, comments, and flags.
    """
    # Check if current user is following
    is_following = any(f.user_id == current_user.id for f in ticket.followers)

    # Filter internal comments for citizens
    comments = ticket.comments
    if current_user.role == UserRole.CITIZEN:
        comments = [c for c in comments if not c.is_internal]

    # Sort comments by created_at descending (most recent first)
    comments = sorted(comments, key=lambda c: c.created_at, reverse=True)

    # Build CommentResponse objects with user_name from relationship
    comment_responses = [
        CommentResponse(
            id=c.id,
            ticket_id=c.ticket_id,
            user_id=c.user_id,
            user_name=c.user.name if c.user else None,
            content=c.content,
            is_internal=c.is_internal,
            created_at=c.created_at,
        )
        for c in comments
    ]

    # Build StatusLogResponse objects with changed_by_name from relationship
    status_log_responses = [
        StatusLogResponse(
            id=log.id,
            ticket_id=log.ticket_id,
            old_status=log.old_status,
            new_status=log.new_status,
            changed_by_id=log.changed_by_id,
            changed_by_name=log.changed_by.name if log.changed_by else None,
            comment=log.comment,
            created_at=log.created_at,
        )
        for log in sorted(ticket.status_logs, key=lambda x: x.created_at, reverse=True)
    ]

    return TicketDetailResponse(
        id=ticket.id,
        title=ticket.title,
        description=ticket.description,
        status=ticket.status,
        category_id=ticket.category_id,
        category_name=ticket.category.name if ticket.category else None,
        location=ticket.location,
        reporter_id=ticket.reporter_id,
        reporter_name=ticket.reporter.name if ticket.reporter else None,
        team_id=ticket.team_id,
        team_name=ticket.assigned_team.name if ticket.assigned_team else None,
        resolved_at=ticket.resolved_at,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        photo_count=len(ticket.photos),
        comment_count=len(comments),
        follower_count=len(ticket.followers),
        photos=ticket.photos,
        comments=comment_responses,
        status_logs=status_log_responses,
        has_feedback=ticket.feedback is not None,
        has_escalation=len(ticket.escalations) > 0,
        can_escalate=(
            ticket.team_id is not None
            and not any(e.status == EscalationStatus.PENDING for e in ticket.escalations)
            and not any(e.status == EscalationStatus.APPROVED for e in ticket.escalations)
        ),
        is_following=is_following,
    )


async def get_ticket_by_id(
    db: AsyncSession,
    ticket_id: UUID,
    with_full_relations: bool = False,
) -> Ticket | None:
    """Get a ticket by ID with optional relationship loading.

    Args:
        db: Database session.
        ticket_id: The ticket UUID.
        with_full_relations: If True, loads all relations including feedback/escalation.

    Returns:
        The ticket if found, None otherwise.
    """
    query = select(Ticket).where(
        Ticket.id == ticket_id,
        Ticket.deleted_at.is_(None),
    )

    if with_full_relations:
        query = query.options(
            joinedload(Ticket.category),
            joinedload(Ticket.location),
            joinedload(Ticket.reporter),
            joinedload(Ticket.assigned_team),
            selectinload(Ticket.photos),
            selectinload(Ticket.comments).joinedload(Comment.user),
            selectinload(Ticket.followers),
            selectinload(Ticket.status_logs).joinedload(StatusLog.changed_by),
            selectinload(Ticket.feedback),
            selectinload(Ticket.escalations),
        )
    else:
        query = query.options(
            joinedload(Ticket.category),
            joinedload(Ticket.location),
            joinedload(Ticket.reporter),
            joinedload(Ticket.assigned_team),
            selectinload(Ticket.photos),
            selectinload(Ticket.comments).joinedload(Comment.user),
            selectinload(Ticket.followers),
            selectinload(Ticket.status_logs).joinedload(StatusLog.changed_by),
        )

    result = await db.execute(query)
    return result.scalar_one_or_none()


def get_ticket_list_query():
    """Get base query for listing tickets with standard relations.

    Returns:
        SQLAlchemy select query with joinedload/selectinload options.
    """
    return (
        select(Ticket)
        .where(Ticket.deleted_at.is_(None))
        .options(
            joinedload(Ticket.category),
            joinedload(Ticket.location),
            joinedload(Ticket.reporter),
            joinedload(Ticket.assigned_team),
            selectinload(Ticket.photos),
            selectinload(Ticket.comments).joinedload(Comment.user),
            selectinload(Ticket.followers),
        )
    )
