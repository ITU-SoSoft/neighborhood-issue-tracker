"""Feedback API routes."""

from uuid import UUID

from fastapi import APIRouter, status
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.api.deps import CurrentUser, DatabaseSession
from app.core.exceptions import (
    FeedbackAlreadyExistsException,
    ForbiddenException,
    TicketNotFoundException,
)
from app.models.feedback import Feedback
from app.models.ticket import Ticket, TicketStatus
from app.schemas.feedback import FeedbackCreate, FeedbackResponse

router = APIRouter()


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
    )
