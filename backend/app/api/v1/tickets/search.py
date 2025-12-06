"""Ticket search endpoints - nearby ticket search."""

from uuid import UUID

from fastapi import APIRouter, Query, status
from geoalchemy2.functions import (
    ST_Distance,
    ST_DWithin,
    ST_MakePoint,
    ST_SetSRID,
    ST_Transform,
)
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
    Uses ST_Transform to convert to Web Mercator (3857) for meter-based distance calculation.
    """
    # Create a PostGIS point for the search location (WGS84 - SRID 4326)
    search_point_wgs84 = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
    
    # Transform to Web Mercator (SRID 3857) for meter-based distance calculation
    # Web Mercator uses meters as units, so ST_Distance will return meters
    search_point_mercator = ST_Transform(search_point_wgs84, 3857)
    location_mercator = ST_Transform(Location.coordinates, 3857)
    
    # Calculate distance in meters using Web Mercator coordinates
    distance_expr = ST_Distance(location_mercator, search_point_mercator)
    
    # Build base query
    query = (
        select(
            Ticket,
            distance_expr.label("distance"),
        )
        .join(Location, Ticket.location_id == Location.id)
        .join(Category, Ticket.category_id == Category.id)
        .where(
            Ticket.deleted_at.is_(None),
            Ticket.status.in_([TicketStatus.NEW, TicketStatus.IN_PROGRESS]),
        )
    )

    if category_id:
        query = query.where(Ticket.category_id == category_id)

    # Pre-filter using ST_DWithin in Web Mercator (meters) to reduce calculations
    # Use a slightly larger radius (1.5x) to ensure we don't miss edge cases
    expanded_radius = radius_meters * 1.5
    
    query = query.where(
        ST_DWithin(
            location_mercator,
            search_point_mercator,
            expanded_radius
        )
    )

    # Order by distance to get closest tickets first
    query = query.order_by(distance_expr).limit(50)

    result = await db.execute(query)
    rows = result.all()

    nearby = []
    for ticket, distance_meters in rows:
        # Filter by exact radius (distance is in meters from ST_Distance_Sphere)
        if distance_meters is None or distance_meters > radius_meters:
            continue

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
                distance_meters=float(distance_meters),
                follower_count=follower_count,
            )
        )

        # Limit to 10 results
        if len(nearby) >= 10:
            break

    return nearby
