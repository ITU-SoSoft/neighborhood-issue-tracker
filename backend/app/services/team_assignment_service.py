"""Team assignment service for automatic ticket routing."""

import uuid
from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.district import District
from app.models.team import Team, TeamCategory, TeamDistrict


class TeamAssignmentService:
    """Service for automatic team assignment based on location and category."""

    @staticmethod
    async def find_matching_team(
        session: AsyncSession,
        category_id: uuid.UUID,
        district: Optional[str],
        city: str,
    ) -> Optional[Team]:
        """
        Find the best matching team for a ticket based on category and location.
        
        Priority:
        1. Team that handles both the category AND district
        2. Team that handles the category (any district in the city)
        3. Team that handles the category (no district filtering)
        4. None (manual assignment required)
        
        Args:
            session: Database session
            category_id: Category UUID
            district: District name (optional)
            city: City name
            
        Returns:
            Matching Team or None
        """
        
        # Priority 1: Find teams that handle both category and district
        if district:
            # First, find the district ID
            district_query = select(District).where(
                and_(
                    District.name == district,
                    District.city == city,
                )
            )
            district_result = await session.execute(district_query)
            district_obj = district_result.scalar_one_or_none()
            
            if district_obj:
                query = (
                    select(Team)
                    .join(TeamCategory, Team.id == TeamCategory.team_id)
                    .join(TeamDistrict, Team.id == TeamDistrict.team_id)
                    .where(
                        and_(
                            TeamCategory.category_id == category_id,
                            TeamDistrict.district_id == district_obj.id,
                        )
                    )
                    .limit(1)
                )
                result = await session.execute(query)
                team = result.scalar_one_or_none()
                if team:
                    return team

        # Priority 2: Find teams that handle the category (any district in the city)
        query = (
            select(Team)
            .join(TeamCategory, Team.id == TeamCategory.team_id)
            .join(TeamDistrict, Team.id == TeamDistrict.team_id)
            .join(District, TeamDistrict.district_id == District.id)
            .where(
                and_(
                    TeamCategory.category_id == category_id,
                    District.city == city,
                )
            )
            .limit(1)
        )
        result = await session.execute(query)
        team = result.scalar_one_or_none()
        if team:
            return team

        # Priority 3: Find teams that handle the category (no district filtering)
        query = (
            select(Team)
            .join(TeamCategory, Team.id == TeamCategory.team_id)
            .where(TeamCategory.category_id == category_id)
            .limit(1)
        )
        result = await session.execute(query)
        team = result.scalar_one_or_none()
        
        return team

    @staticmethod
    async def get_team_workload(session: AsyncSession, team_id: uuid.UUID) -> int:
        """Get the number of active tickets assigned to a team."""
        from app.models.ticket import Ticket, TicketStatus
        
        query = select(Ticket).where(
            and_(
                Ticket.team_id == team_id,
                Ticket.status.in_([TicketStatus.NEW, TicketStatus.IN_PROGRESS]),
                Ticket.deleted_at.is_(None),
            )
        )
        result = await session.execute(query)
        tickets = result.scalars().all()
        return len(tickets)

