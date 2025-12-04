"""Ticket status transition endpoint."""

from uuid import UUID

from fastapi import APIRouter, status

from app.api.deps import DatabaseSession, SupportUser
from app.core.exceptions import TicketNotFoundException
from app.schemas.ticket import TicketResponse, TicketStatusUpdate
from app.services.sms import sms_service
from app.services.ticket_query_service import build_ticket_response, get_ticket_by_id
from app.services.ticket_service import ticket_service

router = APIRouter()


@router.patch(
    "/{ticket_id}/status",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
)
async def update_ticket_status(
    ticket_id: UUID,
    request: TicketStatusUpdate,
    current_user: SupportUser,
    db: DatabaseSession,
) -> TicketResponse:
    """Update ticket status (support/manager only)."""
    ticket = await get_ticket_by_id(db, ticket_id)

    if ticket is None:
        raise TicketNotFoundException()

    ticket = await ticket_service.update_status(
        db, ticket, request.status, request.comment, current_user
    )

    # Send SMS notification to reporter and followers
    if ticket.reporter:
        await sms_service.send_ticket_status_update(
            ticket.reporter.phone_number,
            str(ticket.id),
            request.status.value,
        )

    return build_ticket_response(ticket, current_user)
