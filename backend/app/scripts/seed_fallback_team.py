"""Create fallback team for unassigned tickets."""
import asyncio
import logging

from sqlalchemy import select

from app.database import async_session_maker
from app.models.category import Category
from app.models.district import District
from app.models.team import Team, TeamCategory, TeamDistrict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FALLBACK_TEAM_NAME = "Istanbul General Team"


async def create_fallback_team() -> None:
    """Create a fallback team that handles all unassigned tickets."""
    async with async_session_maker() as session:
        # Check if fallback team already exists
        result = await session.execute(
            select(Team).where(Team.name == FALLBACK_TEAM_NAME)
        )
        existing_team = result.scalar_one_or_none()
        
        if existing_team:
            logger.info(f"✅ Fallback team already exists: {FALLBACK_TEAM_NAME}")
            return
        
        # Create fallback team
        team = Team(
            name=FALLBACK_TEAM_NAME,
            description="General team that handles unassigned tickets from deleted teams. This team cannot be deleted.",
        )
        session.add(team)
        await session.flush()
        
        # Assign ALL categories to this team
        result = await session.execute(select(Category))
        all_categories = result.scalars().all()
        
        for category in all_categories:
            team_category = TeamCategory(
                team_id=team.id,
                category_id=category.id,
            )
            session.add(team_category)
            logger.info(f"  Added category: {category.name}")
        
        # Assign ALL Istanbul districts to this team
        result = await session.execute(
            select(District).where(District.city == "Istanbul")
        )
        all_districts = result.scalars().all()
        
        for district in all_districts:
            team_district = TeamDistrict(
                team_id=team.id,
                district_id=district.id,
            )
            session.add(team_district)
            logger.info(f"  Added district: {district.name}")
        
        await session.commit()
        
        logger.info("="*60)
        logger.info(f"✅ Created fallback team: {FALLBACK_TEAM_NAME}")
        logger.info(f"   Categories: {len(all_categories)}")
        logger.info(f"   Districts: {len(all_districts)}")
        logger.info("   Purpose: Catches all unassigned tickets")
        logger.info("   Note: This team CANNOT be deleted")
        logger.info("="*60)


async def assign_unassigned_tickets_to_fallback() -> None:
    """Assign all currently unassigned tickets to the fallback team."""
    async with async_session_maker() as session:
        from app.models.ticket import Ticket
        
        # Get fallback team
        result = await session.execute(
            select(Team).where(Team.name == FALLBACK_TEAM_NAME)
        )
        fallback_team = result.scalar_one_or_none()
        
        if not fallback_team:
            logger.error("❌ Fallback team not found!")
            return
        
        # Get all unassigned tickets
        result = await session.execute(
            select(Ticket).where(
                Ticket.team_id.is_(None),
                Ticket.deleted_at.is_(None),
            )
        )
        unassigned_tickets = result.scalars().all()
        
        if not unassigned_tickets:
            logger.info("✅ No unassigned tickets to assign")
            return
        
        # Assign to fallback team
        for ticket in unassigned_tickets:
            ticket.team_id = fallback_team.id
            logger.info(f"  Assigned ticket: {ticket.title} → {FALLBACK_TEAM_NAME}")
        
        await session.commit()
        
        logger.info("="*60)
        logger.info(f"✅ Assigned {len(unassigned_tickets)} tickets to fallback team")
        logger.info("="*60)


async def main():
    """Main entry point."""
    logger.info("🌱 Creating fallback team...")
    await create_fallback_team()
    
    logger.info("\n📌 Assigning unassigned tickets...")
    await assign_unassigned_tickets_to_fallback()


if __name__ == "__main__":
    asyncio.run(main())

