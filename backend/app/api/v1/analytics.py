"""Analytics API endpoints for managers."""

from datetime import datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, case, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import DatabaseSession, ManagerUser
from app.models.category import Category
from app.models.feedback import Feedback
from app.models.team import Team
from app.models.ticket import Location, Ticket, TicketStatus
from app.models.user import User, UserRole
from app.schemas.analytics import (
    CategoryStats,
    CategoryStatsResponse,
    DashboardKPIs,
    HeatmapPoint,
    HeatmapResponse,
    MemberPerformance,
    MemberPerformanceResponse,
    TeamPerformance,
    TeamPerformanceResponse,
)

router = APIRouter()


@router.get("/dashboard", response_model=DashboardKPIs)
async def get_dashboard_kpis(
    db: DatabaseSession,
    current_user: ManagerUser,
    days: Annotated[int, Query(ge=1, le=365)] = 30,
) -> DashboardKPIs:
    """Get dashboard key performance indicators.

    Args:
        db: Database session.
        current_user: The authenticated manager user.
        days: Number of days to look back for statistics.

    Returns:
        Dashboard KPIs including ticket counts, resolution rate, etc.
    """
    start_date = datetime.utcnow() - timedelta(days=days)

    # Base query for tickets within the date range
    base_query = select(Ticket).where(
        and_(
            Ticket.created_at >= start_date,
            Ticket.deleted_at.is_(None),
        )
    )

    # Total tickets
    total_result = await db.execute(
        select(func.count(Ticket.id)).where(
            and_(
                Ticket.created_at >= start_date,
                Ticket.deleted_at.is_(None),
            )
        )
    )
    total_tickets = total_result.scalar() or 0

    # Status counts
    status_counts_result = await db.execute(
        select(Ticket.status, func.count(Ticket.id))
        .where(
            and_(
                Ticket.created_at >= start_date,
                Ticket.deleted_at.is_(None),
            )
        )
        .group_by(Ticket.status)
    )
    status_counts = dict(status_counts_result.all())

    open_tickets = status_counts.get(TicketStatus.NEW, 0) + status_counts.get(
        TicketStatus.IN_PROGRESS, 0
    )
    resolved_tickets = status_counts.get(TicketStatus.RESOLVED, 0)
    closed_tickets = status_counts.get(TicketStatus.CLOSED, 0)
    escalated_tickets = status_counts.get(TicketStatus.ESCALATED, 0)

    # Resolution rate
    resolution_rate = 0.0
    if total_tickets > 0:
        resolution_rate = ((resolved_tickets + closed_tickets) / total_tickets) * 100

    # Average rating
    avg_rating_result = await db.execute(
        select(func.avg(Feedback.rating)).where(
            Feedback.ticket_id.in_(
                select(Ticket.id).where(
                    and_(
                        Ticket.created_at >= start_date,
                        Ticket.deleted_at.is_(None),
                    )
                )
            )
        )
    )
    average_rating = avg_rating_result.scalar()

    # Average resolution time in hours
    avg_resolution_result = await db.execute(
        select(
            func.avg(
                func.extract("epoch", Ticket.resolved_at - Ticket.created_at) / 3600
            )
        ).where(
            and_(
                Ticket.created_at >= start_date,
                Ticket.deleted_at.is_(None),
                Ticket.resolved_at.is_not(None),
            )
        )
    )
    average_resolution_hours = avg_resolution_result.scalar()

    return DashboardKPIs(
        total_tickets=total_tickets,
        open_tickets=open_tickets,
        resolved_tickets=resolved_tickets,
        closed_tickets=closed_tickets,
        escalated_tickets=escalated_tickets,
        resolution_rate=round(resolution_rate, 2),
        average_rating=round(average_rating, 2) if average_rating else None,
        average_resolution_hours=(
            round(average_resolution_hours, 2) if average_resolution_hours else None
        ),
    )


@router.get("/heatmap", response_model=HeatmapResponse)
async def get_ticket_heatmap(
    db: DatabaseSession,
    current_user: ManagerUser,
    days: Annotated[int, Query(ge=1, le=365)] = 30,
    category_id: UUID | None = None,
    status: TicketStatus | None = None,
) -> HeatmapResponse:
    """Get heatmap data for ticket locations.

    Args:
        db: Database session.
        current_user: The authenticated manager user.
        days: Number of days to look back.
        category_id: Optional category filter.
        status: Optional status filter.

    Returns:
        Heatmap data with location points and intensity.
    """
    start_date = datetime.utcnow() - timedelta(days=days)

    # Build query with filters
    query = (
        select(
            Location.latitude,
            Location.longitude,
            func.count(Ticket.id).label("count"),
        )
        .join(Ticket, Ticket.location_id == Location.id)
        .where(
            and_(
                Ticket.created_at >= start_date,
                Ticket.deleted_at.is_(None),
            )
        )
        .group_by(Location.latitude, Location.longitude)
    )

    if category_id:
        query = query.where(Ticket.category_id == category_id)

    if status:
        query = query.where(Ticket.status == status)

    result = await db.execute(query)
    rows = result.all()

    if not rows:
        return HeatmapResponse(points=[], total_tickets=0, max_count=0)

    max_count = max(row.count for row in rows)
    total_tickets = sum(row.count for row in rows)

    points = [
        HeatmapPoint(
            latitude=row.latitude,
            longitude=row.longitude,
            count=row.count,
            intensity=row.count / max_count if max_count > 0 else 0.0,
        )
        for row in rows
    ]

    return HeatmapResponse(
        points=points,
        total_tickets=total_tickets,
        max_count=max_count,
    )


@router.get("/teams", response_model=TeamPerformanceResponse)
async def get_team_performance(
    db: DatabaseSession,
    current_user: ManagerUser,
    days: Annotated[int, Query(ge=1, le=365)] = 30,
) -> TeamPerformanceResponse:
    """Get performance metrics for all teams.

    Args:
        db: Database session.
        current_user: The authenticated manager user.
        days: Number of days to look back.

    Returns:
        Performance metrics for all teams.
    """
    start_date = datetime.utcnow() - timedelta(days=days)

    # Get all teams
    teams_result = await db.execute(select(Team))
    teams = teams_result.scalars().all()

    team_performances = []

    for team in teams:
        # Get team member IDs
        members_result = await db.execute(
            select(User.id).where(
                and_(
                    User.team_id == team.id,
                    User.deleted_at.is_(None),
                )
            )
        )
        member_ids = [row[0] for row in members_result.all()]
        member_count = len(member_ids)

        if not member_ids:
            team_performances.append(
                TeamPerformance(
                    team_id=team.id,
                    team_name=team.name,
                    total_assigned=0,
                    total_resolved=0,
                    resolution_rate=0.0,
                    average_resolution_hours=None,
                    average_rating=None,
                    member_count=0,
                )
            )
            continue

        # Total assigned to team members
        total_assigned_result = await db.execute(
            select(func.count(Ticket.id)).where(
                and_(
                    Ticket.team_id == team.id,
                    Ticket.created_at >= start_date,
                    Ticket.deleted_at.is_(None),
                )
            )
        )
        total_assigned = total_assigned_result.scalar() or 0

        # Total resolved by team members
        total_resolved_result = await db.execute(
            select(func.count(Ticket.id)).where(
                and_(
                    Ticket.team_id == team.id,
                    Ticket.created_at >= start_date,
                    Ticket.deleted_at.is_(None),
                    Ticket.status.in_([TicketStatus.RESOLVED, TicketStatus.CLOSED]),
                )
            )
        )
        total_resolved = total_resolved_result.scalar() or 0

        # Resolution rate
        resolution_rate = 0.0
        if total_assigned > 0:
            resolution_rate = (total_resolved / total_assigned) * 100

        # Average resolution hours
        avg_resolution_result = await db.execute(
            select(
                func.avg(
                    func.extract("epoch", Ticket.resolved_at - Ticket.created_at) / 3600
                )
            ).where(
                and_(
                    Ticket.team_id == team.id,
                    Ticket.created_at >= start_date,
                    Ticket.deleted_at.is_(None),
                    Ticket.resolved_at.is_not(None),
                )
            )
        )
        average_resolution_hours = avg_resolution_result.scalar()

        # Average rating
        avg_rating_result = await db.execute(
            select(func.avg(Feedback.rating)).where(
                Feedback.ticket_id.in_(
                    select(Ticket.id).where(
                        and_(
                            Ticket.team_id == team.id,
                            Ticket.created_at >= start_date,
                            Ticket.deleted_at.is_(None),
                        )
                    )
                )
            )
        )
        average_rating = avg_rating_result.scalar()

        team_performances.append(
            TeamPerformance(
                team_id=team.id,
                team_name=team.name,
                total_assigned=total_assigned,
                total_resolved=total_resolved,
                resolution_rate=round(resolution_rate, 2),
                average_resolution_hours=(
                    round(average_resolution_hours, 2)
                    if average_resolution_hours
                    else None
                ),
                average_rating=round(average_rating, 2) if average_rating else None,
                member_count=member_count,
            )
        )

    return TeamPerformanceResponse(teams=team_performances)


@router.get("/teams/{team_id}/members", response_model=MemberPerformanceResponse)
async def get_team_member_performance(
    team_id: UUID,
    db: DatabaseSession,
    current_user: ManagerUser,
    days: Annotated[int, Query(ge=1, le=365)] = 30,
) -> MemberPerformanceResponse:
    """Get performance metrics for team members.

    Args:
        team_id: The team ID.
        db: Database session.
        current_user: The authenticated manager user.
        days: Number of days to look back.

    Returns:
        Performance metrics for team members.
    """
    from app.core.exceptions import NotFoundException

    start_date = datetime.utcnow() - timedelta(days=days)

    # Verify team exists
    team_result = await db.execute(select(Team).where(Team.id == team_id))
    team = team_result.scalar_one_or_none()

    if not team:
        raise NotFoundException(detail="Team not found")

    # Get team members
    members_result = await db.execute(
        select(User).where(
            and_(
                User.team_id == team_id,
                User.deleted_at.is_(None),
            )
        )
    )
    members = members_result.scalars().all()

    member_performances = []

    for member in members:
        # Total assigned
        total_assigned_result = await db.execute(
            select(func.count(Ticket.id)).where(
                and_(
                    Ticket.team_id == member.team_id,
                    Ticket.created_at >= start_date,
                    Ticket.deleted_at.is_(None),
                )
            )
        )
        total_assigned = total_assigned_result.scalar() or 0

        # Total resolved
        total_resolved_result = await db.execute(
            select(func.count(Ticket.id)).where(
                and_(
                    Ticket.team_id == member.team_id,
                    Ticket.created_at >= start_date,
                    Ticket.deleted_at.is_(None),
                    Ticket.status.in_([TicketStatus.RESOLVED, TicketStatus.CLOSED]),
                )
            )
        )
        total_resolved = total_resolved_result.scalar() or 0

        # Resolution rate
        resolution_rate = 0.0
        if total_assigned > 0:
            resolution_rate = (total_resolved / total_assigned) * 100

        # Average resolution hours
        avg_resolution_result = await db.execute(
            select(
                func.avg(
                    func.extract("epoch", Ticket.resolved_at - Ticket.created_at) / 3600
                )
            ).where(
                and_(
                    Ticket.team_id == member.team_id,
                    Ticket.created_at >= start_date,
                    Ticket.deleted_at.is_(None),
                    Ticket.resolved_at.is_not(None),
                )
            )
        )
        average_resolution_hours = avg_resolution_result.scalar()

        # Average rating
        avg_rating_result = await db.execute(
            select(func.avg(Feedback.rating)).where(
                Feedback.ticket_id.in_(
                    select(Ticket.id).where(
                        and_(
                            Ticket.team_id == member.team_id,
                            Ticket.created_at >= start_date,
                            Ticket.deleted_at.is_(None),
                        )
                    )
                )
            )
        )
        average_rating = avg_rating_result.scalar()

        member_performances.append(
            MemberPerformance(
                user_id=member.id,
                user_name=member.name or member.phone_number,
                total_assigned=total_assigned,
                total_resolved=total_resolved,
                resolution_rate=round(resolution_rate, 2),
                average_resolution_hours=(
                    round(average_resolution_hours, 2)
                    if average_resolution_hours
                    else None
                ),
                average_rating=round(average_rating, 2) if average_rating else None,
            )
        )

    return MemberPerformanceResponse(
        members=member_performances,
        team_id=team.id,
        team_name=team.name,
    )


@router.get("/categories", response_model=CategoryStatsResponse)
async def get_category_statistics(
    db: DatabaseSession,
    current_user: ManagerUser,
    days: Annotated[int, Query(ge=1, le=365)] = 30,
) -> CategoryStatsResponse:
    """Get statistics by category.

    Args:
        db: Database session.
        current_user: The authenticated manager user.
        days: Number of days to look back.

    Returns:
        Statistics for each category.
    """
    start_date = datetime.utcnow() - timedelta(days=days)

    # Get all categories
    categories_result = await db.execute(
        select(Category).where(Category.is_active == True)
    )
    categories = categories_result.scalars().all()

    category_stats = []

    for category in categories:
        # Total tickets
        total_result = await db.execute(
            select(func.count(Ticket.id)).where(
                and_(
                    Ticket.category_id == category.id,
                    Ticket.created_at >= start_date,
                    Ticket.deleted_at.is_(None),
                )
            )
        )
        total_tickets = total_result.scalar() or 0

        # Open tickets
        open_result = await db.execute(
            select(func.count(Ticket.id)).where(
                and_(
                    Ticket.category_id == category.id,
                    Ticket.created_at >= start_date,
                    Ticket.deleted_at.is_(None),
                    Ticket.status.in_([TicketStatus.NEW, TicketStatus.IN_PROGRESS]),
                )
            )
        )
        open_tickets = open_result.scalar() or 0

        # Resolved tickets
        resolved_result = await db.execute(
            select(func.count(Ticket.id)).where(
                and_(
                    Ticket.category_id == category.id,
                    Ticket.created_at >= start_date,
                    Ticket.deleted_at.is_(None),
                    Ticket.status.in_([TicketStatus.RESOLVED, TicketStatus.CLOSED]),
                )
            )
        )
        resolved_tickets = resolved_result.scalar() or 0

        # Average rating
        avg_rating_result = await db.execute(
            select(func.avg(Feedback.rating)).where(
                Feedback.ticket_id.in_(
                    select(Ticket.id).where(
                        and_(
                            Ticket.category_id == category.id,
                            Ticket.created_at >= start_date,
                            Ticket.deleted_at.is_(None),
                        )
                    )
                )
            )
        )
        average_rating = avg_rating_result.scalar()

        category_stats.append(
            CategoryStats(
                category_id=category.id,
                category_name=category.name,
                total_tickets=total_tickets,
                open_tickets=open_tickets,
                resolved_tickets=resolved_tickets,
                average_rating=round(average_rating, 2) if average_rating else None,
            )
        )

    return CategoryStatsResponse(categories=category_stats)
