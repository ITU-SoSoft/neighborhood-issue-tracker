"""Ticket CRUD endpoints - create, list, get, update."""

from uuid import UUID

from fastapi import APIRouter, Query, status
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DatabaseSession, SupportUser
from app.core.exceptions import TicketNotFoundException
from app.models.ticket import Ticket, TicketStatus
from app.schemas.ticket import (
    TicketCreate,
    TicketDetailResponse,
    TicketListResponse,
    TicketResponse,
    TicketUpdate,
)
from app.services.ticket_query_service import (
    build_ticket_detail_response,
    build_ticket_response,
    get_ticket_by_id,
    get_ticket_list_query,
)
from app.services.ticket_service import ticket_service

router = APIRouter()


@router.post(
    "/",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_ticket(
    request: TicketCreate,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> TicketResponse:
    """Create a new ticket (citizens only)."""
    ticket = await ticket_service.create_ticket(db, request, current_user)
    return build_ticket_response(ticket, current_user)


@router.get(
    "/",
    response_model=TicketListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_tickets(
    current_user: SupportUser,
    db: DatabaseSession,
    status_filter: TicketStatus | None = None,
    category_id: UUID | None = None,
    team_id: UUID | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> TicketListResponse:
    """List all tickets (support/manager only).

    Supports filtering by status, category, and team.
    """
    query = select(Ticket).where(Ticket.deleted_at.is_(None))

    if status_filter:
        query = query.where(Ticket.status == status_filter)
    if category_id:
        query = query.where(Ticket.category_id == category_id)
    if team_id:
        query = query.where(Ticket.team_id == team_id)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Get paginated results with relationships
    query = (
        get_ticket_list_query()
        .where(Ticket.deleted_at.is_(None))
        .order_by(Ticket.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    # Apply filters again on the full query
    if status_filter:
        query = query.where(Ticket.status == status_filter)
    if category_id:
        query = query.where(Ticket.category_id == category_id)
    if team_id:
        query = query.where(Ticket.team_id == team_id)

    result = await db.execute(query)
    tickets = result.unique().scalars().all()

    return TicketListResponse(
        items=[build_ticket_response(t, current_user) for t in tickets],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{ticket_id}",
    response_model=TicketDetailResponse,
    status_code=status.HTTP_200_OK,
)
async def get_ticket(
    ticket_id: UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> TicketDetailResponse:
    """Get ticket details by ID."""
    ticket = await get_ticket_by_id(db, ticket_id, with_full_relations=True)

    if ticket is None:
        raise TicketNotFoundException()

    return build_ticket_detail_response(ticket, current_user)


@router.patch(
    "/{ticket_id}",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
)
async def update_ticket(
    ticket_id: UUID,
    request: TicketUpdate,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> TicketResponse:
    """Update ticket details (title, description, category).

    - Citizens can only update their own tickets that are still NEW.
    - Support/Manager can update any ticket that is not CLOSED.
    """
    ticket = await get_ticket_by_id(db, ticket_id)

    if ticket is None:
        raise TicketNotFoundException()

    ticket = await ticket_service.update_ticket(db, ticket, request, current_user)
    return build_ticket_response(ticket, current_user)


@router.delete(
    "/{ticket_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_ticket(
    ticket_id: UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> None:
    """Delete a ticket (soft delete).

    Citizens can only delete their own NEW tickets.
    """
    await ticket_service.delete_ticket(db, ticket_id, current_user)
