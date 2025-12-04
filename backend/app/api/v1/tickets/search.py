"""Ticket search endpoints - nearby ticket search."""

from uuid import UUID

from fastapi import APIRouter, Query, status
from geoalchemy2.functions import ST_DWithin, ST_Distance, ST_MakePoint, ST_SetSRID
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DatabaseSession
from app.models.category import Category
from app.models.ticket import Location, Ticket, TicketFollower, TicketStatus
from app.schemas.ticket import NearbyTicketResponse

router = APIRouter()


@router.get(
    "/nearby",
    response_model=list[NearbyTicketResponse],
    status_code=status.HTTP_200_OK,
)
async def find_nearby_tickets(
    current_user: CurrentUser,
    db: DatabaseSession,
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_meters: int = Query(default=500, ge=100, le=5000),
    category_id: UUID | None = None,
) -> list[NearbyTicketResponse]:
    """Find tickets near a location.

    Used to detect potential duplicates when creating a new ticket.
    """
    # Create a PostGIS point for the search location
    search_point = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)

    # Query for nearby tickets
    query = (
        select(
            Ticket,
            ST_Distance(Location.coordinates, search_point).label("distance"),
        )
        .join(Location, Ticket.location_id == Location.id)
        .join(Category, Ticket.category_id == Category.id)
        .where(
            Ticket.deleted_at.is_(None),
            Ticket.status.in_([TicketStatus.NEW, TicketStatus.IN_PROGRESS]),
            ST_DWithin(Location.coordinates, search_point, radius_meters),
        )
    )

    if category_id:
        query = query.where(Ticket.category_id == category_id)

    query = query.order_by("distance").limit(10)

    result = await db.execute(query)
    rows = result.all()

    nearby = []
    for ticket, distance in rows:
        # Load category name
        cat_result = await db.execute(
            select(Category.name).where(Category.id == ticket.category_id)
        )
        category_name = cat_result.scalar_one_or_none() or "Unknown"

        # Count followers
        follower_result = await db.execute(
            select(func.count()).where(TicketFollower.ticket_id == ticket.id)
        )
        follower_count = follower_result.scalar() or 0

        nearby.append(
            NearbyTicketResponse(
                id=ticket.id,
                title=ticket.title,
                status=ticket.status,
                category_name=category_name,
                distance_meters=distance,
                follower_count=follower_count,
            )
        )

    return nearby
