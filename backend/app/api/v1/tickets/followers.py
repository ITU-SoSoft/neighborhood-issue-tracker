"""Ticket follow/unfollow endpoints."""

from uuid import UUID

from fastapi import APIRouter, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DatabaseSession
from app.core.exceptions import TicketNotFoundException
from app.models.ticket import Ticket, TicketFollower
from app.services.notification_service import notify_ticket_followed

router = APIRouter()


@router.post(
    "/{ticket_id}/follow",
    status_code=status.HTTP_201_CREATED,
)
async def follow_ticket(
    ticket_id: UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> dict:
    """Follow a ticket to receive updates."""
    result = await db.execute(
        select(Ticket).where(Ticket.id == ticket_id, Ticket.deleted_at.is_(None))
    )
    ticket = result.scalar_one_or_none()

    if ticket is None:
        raise TicketNotFoundException()

    # Check if already following
    result = await db.execute(
        select(TicketFollower).where(
            TicketFollower.ticket_id == ticket_id,
            TicketFollower.user_id == current_user.id,
        )
    )
    if result.scalar_one_or_none():
        return {"message": "Already following this ticket"}

    # Create follower record
    follower = TicketFollower(
        ticket_id=ticket_id,
        user_id=current_user.id,
    )
    db.add(follower)
    await db.commit()

    # Send notification to ticket reporter
    try:
        await notify_ticket_followed(db, ticket, current_user)
    except Exception:
        # Don't fail follow if notification fails
        pass

    return {"message": "Now following this ticket"}


@router.delete(
    "/{ticket_id}/follow",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def unfollow_ticket(
    ticket_id: UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> None:
    """Unfollow a ticket."""
    result = await db.execute(
        select(TicketFollower).where(
            TicketFollower.ticket_id == ticket_id,
            TicketFollower.user_id == current_user.id,
        )
    )
    follower = result.scalar_one_or_none()

    if follower:
        await db.delete(follower)
        await db.commit()
