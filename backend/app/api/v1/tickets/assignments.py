"""Ticket assignment endpoints - my tickets, assigned tickets, assign ticket."""

from uuid import UUID

from fastapi import APIRouter, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import joinedload, selectinload

from app.api.deps import CurrentUser, DatabaseSession, ManagerUser, SupportUser
from app.core.exceptions import TicketNotFoundException
from app.models.ticket import Ticket, TicketFollower, TicketStatus
from app.schemas.ticket import TicketAssignUpdate, TicketListResponse, TicketResponse
from app.services.ticket_query_service import build_ticket_response, get_ticket_by_id
from app.services.ticket_service import ticket_service

router = APIRouter()


@router.get(
    "/my",
    response_model=TicketListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_my_tickets(
    current_user: CurrentUser,
    db: DatabaseSession,
    status_filter: TicketStatus | None = None,
    category_id: UUID | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> TicketListResponse:
    """List tickets created by the current user."""
    query = select(Ticket).where(
        Ticket.reporter_id == current_user.id,
        Ticket.deleted_at.is_(None),
    )

    # Apply filters
    if status_filter:
        query = query.where(Ticket.status == status_filter)
    if category_id:
        query = query.where(Ticket.category_id == category_id)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Get paginated results
    query = (
        query.options(
            joinedload(Ticket.category),
            joinedload(Ticket.location),
            selectinload(Ticket.photos),
            selectinload(Ticket.comments),
            selectinload(Ticket.followers),
        )
        .order_by(Ticket.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    result = await db.execute(query)
    tickets = result.unique().scalars().all()

    return TicketListResponse(
        items=[build_ticket_response(t, current_user) for t in tickets],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/assigned",
    response_model=TicketListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_assigned_tickets(
    current_user: SupportUser,
    db: DatabaseSession,
    status_filter: TicketStatus | None = None,
    category_id: UUID | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> TicketListResponse:
    """List tickets assigned to the current support user."""
    query = select(Ticket).where(
        Ticket.assignee_id == current_user.id,
        Ticket.deleted_at.is_(None),
    )

    # Apply filters
    if status_filter:
        query = query.where(Ticket.status == status_filter)
    if category_id:
        query = query.where(Ticket.category_id == category_id)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Get paginated results
    query = (
        query.options(
            joinedload(Ticket.category),
            joinedload(Ticket.location),
            joinedload(Ticket.reporter),
            selectinload(Ticket.photos),
            selectinload(Ticket.comments),
            selectinload(Ticket.followers),
        )
        .order_by(Ticket.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    result = await db.execute(query)
    tickets = result.unique().scalars().all()

    return TicketListResponse(
        items=[build_ticket_response(t, current_user) for t in tickets],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/followed",
    response_model=TicketListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_followed_tickets(
    current_user: CurrentUser,
    db: DatabaseSession,
    status_filter: TicketStatus | None = None,
    category_id: UUID | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> TicketListResponse:
    """List tickets that the current user is following (excluding own tickets)."""
    # Get ticket IDs that the user is following
    follower_query = select(TicketFollower.ticket_id).where(
        TicketFollower.user_id == current_user.id
    )
    followed_ticket_ids = (await db.execute(follower_query)).scalars().all()

    if not followed_ticket_ids:
        return TicketListResponse(
            items=[],
            total=0,
            page=page,
            page_size=page_size,
        )

    # Query tickets that are being followed, but exclude own tickets
    query = select(Ticket).where(
        Ticket.id.in_(followed_ticket_ids),
        Ticket.reporter_id != current_user.id,  # Only tickets created by others
        Ticket.deleted_at.is_(None),
    )

    # Apply filters
    if status_filter:
        query = query.where(Ticket.status == status_filter)
    if category_id:
        query = query.where(Ticket.category_id == category_id)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Get paginated results
    query = (
        query.options(
            joinedload(Ticket.category),
            joinedload(Ticket.location),
            joinedload(Ticket.reporter),
            selectinload(Ticket.photos),
            selectinload(Ticket.comments),
            selectinload(Ticket.followers),
        )
        .order_by(Ticket.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    result = await db.execute(query)
    tickets = result.unique().scalars().all()

    return TicketListResponse(
        items=[build_ticket_response(t, current_user) for t in tickets],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/all",
    response_model=TicketListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_all_user_tickets(
    current_user: CurrentUser,
    db: DatabaseSession,
    status_filter: TicketStatus | None = None,
    category_id: UUID | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> TicketListResponse:
    """List all tickets relevant to the user: own tickets + followed tickets."""
    # Get ticket IDs that the user is following
    follower_query = select(TicketFollower.ticket_id).where(
        TicketFollower.user_id == current_user.id
    )
    followed_ticket_ids = (await db.execute(follower_query)).scalars().all()

    # Build query: own tickets OR followed tickets
    if followed_ticket_ids:
        # Own tickets OR followed tickets
        query = select(Ticket).where(
            Ticket.deleted_at.is_(None),
            or_(
                Ticket.reporter_id == current_user.id,  # Own tickets
                Ticket.id.in_(followed_ticket_ids),  # Followed tickets
            ),
        )
    else:
        # Only own tickets if not following any
        query = select(Ticket).where(
            Ticket.reporter_id == current_user.id,
            Ticket.deleted_at.is_(None),
        )

    # Apply filters
    if status_filter:
        query = query.where(Ticket.status == status_filter)
    if category_id:
        query = query.where(Ticket.category_id == category_id)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Get paginated results
    query = (
        query.options(
            joinedload(Ticket.category),
            joinedload(Ticket.location),
            joinedload(Ticket.reporter),
            selectinload(Ticket.photos),
            selectinload(Ticket.comments),
            selectinload(Ticket.followers),
        )
        .order_by(Ticket.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    result = await db.execute(query)
    tickets = result.unique().scalars().all()

    return TicketListResponse(
        items=[build_ticket_response(t, current_user) for t in tickets],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.patch(
    "/{ticket_id}/assign",
    response_model=TicketResponse,
    status_code=status.HTTP_200_OK,
)
async def assign_ticket(
    ticket_id: UUID,
    request: TicketAssignUpdate,
    current_user: ManagerUser,
    db: DatabaseSession,
) -> TicketResponse:
    """Assign a ticket to a support member (manager only)."""
    ticket = await get_ticket_by_id(db, ticket_id)

    if ticket is None:
        raise TicketNotFoundException()

    ticket = await ticket_service.assign_ticket(db, ticket, request.assignee_id)
    return build_ticket_response(ticket, current_user)
