"""Feedback API routes."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, status
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.api.deps import CurrentUser, DatabaseSession
from app.core.exceptions import (
    FeedbackAlreadyExistsException,
    FeedbackNotFoundException,
    ForbiddenException,
    TicketNotFoundException,
)
from app.models.feedback import Feedback
from app.models.ticket import Ticket, TicketStatus
from app.schemas.feedback import FeedbackCreate, FeedbackResponse, FeedbackUpdate

router = APIRouter()

# Time limit for editing feedback (24 hours)
FEEDBACK_EDIT_WINDOW_HOURS = 24


@router.post(
    "/tickets/{ticket_id}",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_feedback(
    ticket_id: UUID,
    request: FeedbackCreate,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> FeedbackResponse:
    """Submit feedback for a resolved ticket.

    Only the ticket reporter can submit feedback.
    Feedback can only be submitted for resolved or closed tickets.
    """
    # Get ticket with reporter
    result = await db.execute(
        select(Ticket)
        .options(joinedload(Ticket.feedback))
        .where(Ticket.id == ticket_id, Ticket.deleted_at.is_(None))
    )
    ticket = result.scalar_one_or_none()

    if ticket is None:
        raise TicketNotFoundException()

    # Check if user is the reporter
    if ticket.reporter_id != current_user.id:
        raise ForbiddenException(detail="Only the reporter can submit feedback")

    # Check ticket status
    if ticket.status not in (TicketStatus.RESOLVED, TicketStatus.CLOSED):
        raise ForbiddenException(
            detail="Feedback can only be submitted for resolved tickets"
        )

    # Check if feedback already exists
    if ticket.feedback is not None:
        raise FeedbackAlreadyExistsException()

    # Create feedback
    feedback = Feedback(
        ticket_id=ticket_id,
        user_id=current_user.id,
        rating=request.rating,
        comment=request.comment,
    )
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)

    return FeedbackResponse(
        id=feedback.id,
        ticket_id=feedback.ticket_id,
        user_id=feedback.user_id,
        user_name=current_user.name,
        rating=feedback.rating,
        comment=feedback.comment,
        created_at=feedback.created_at,
        updated_at=feedback.updated_at,
    )


@router.get(
    "/tickets/{ticket_id}",
    response_model=FeedbackResponse,
    status_code=status.HTTP_200_OK,
)
async def get_feedback(
    ticket_id: UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> FeedbackResponse:
    """Get feedback for a ticket."""
    result = await db.execute(
        select(Feedback)
        .options(joinedload(Feedback.user))
        .where(Feedback.ticket_id == ticket_id)
    )
    feedback = result.scalar_one_or_none()

    if feedback is None:
        raise TicketNotFoundException()

    return FeedbackResponse(
        id=feedback.id,
        ticket_id=feedback.ticket_id,
        user_id=feedback.user_id,
        user_name=feedback.user.name if feedback.user else None,
        rating=feedback.rating,
        comment=feedback.comment,
        created_at=feedback.created_at,
        updated_at=feedback.updated_at,
    )


@router.patch(
    "/tickets/{ticket_id}",
    response_model=FeedbackResponse,
    status_code=status.HTTP_200_OK,
)
async def update_feedback(
    ticket_id: UUID,
    request: FeedbackUpdate,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> FeedbackResponse:
    """Update feedback for a ticket.

    Only the original feedback author can update their feedback.
    Feedback can only be edited within 24 hours of submission.
    """
    # Get existing feedback
    result = await db.execute(
        select(Feedback)
        .options(joinedload(Feedback.user))
        .where(Feedback.ticket_id == ticket_id)
    )
    feedback = result.scalar_one_or_none()

    if feedback is None:
        raise FeedbackNotFoundException()

    # Check if user is the feedback author
    if feedback.user_id != current_user.id:
        raise ForbiddenException(detail="Only the feedback author can edit feedback")

    # Check if within edit window (24 hours from creation)
    now = datetime.now(timezone.utc)
    edit_deadline = feedback.created_at.replace(tzinfo=timezone.utc) + timedelta(hours=FEEDBACK_EDIT_WINDOW_HOURS)
    
    if now > edit_deadline:
        raise ForbiddenException(
            detail=f"Feedback can only be edited within {FEEDBACK_EDIT_WINDOW_HOURS} hours of submission"
        )

    # Update fields if provided
    if request.rating is not None:
        feedback.rating = request.rating
    if request.comment is not None:
        feedback.comment = request.comment

    # Manually set updated_at since we're updating
    feedback.updated_at = now

    await db.commit()
    await db.refresh(feedback)

    return FeedbackResponse(
        id=feedback.id,
        ticket_id=feedback.ticket_id,
        user_id=feedback.user_id,
        user_name=feedback.user.name if feedback.user else None,
        rating=feedback.rating,
        comment=feedback.comment,
        created_at=feedback.created_at,
        updated_at=feedback.updated_at,
    )
