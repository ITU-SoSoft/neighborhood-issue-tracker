"""Seed teams and team assignments for testing.

Run with: uv run python -m app.scripts.seed_teams
"""

import asyncio
import logging

from sqlalchemy import select

from app.database import async_session_maker
from app.models.category import Category
from app.models.district import District
from app.models.team import Team, TeamCategory, TeamDistrict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample teams for Istanbul
SAMPLE_TEAMS = [
    {
        "name": "Bakırköy Electricity Team",
        "description": "Bakırköy region electricity infrastructure issues",
        "districts": [{"district": "Bakırköy", "city": "Istanbul"}],
        "categories": ["Lighting", "Infrastructure"],
    },
    {
        "name": "Kadıköy Traffic Team",
        "description": "Kadıköy region traffic and road issues",
        "districts": [{"district": "Kadıköy", "city": "Istanbul"}],
        "categories": ["Traffic", "Infrastructure"],
    },
    {
        "name": "Beşiktaş Waste Management Team",
        "description": "Beşiktaş region waste management",
        "districts": [{"district": "Beşiktaş", "city": "Istanbul"}],
        "categories": ["Waste Management"],
    },
    {
        "name": "Şişli Parks Team",
        "description": "Şişli region parks and green area maintenance",
        "districts": [{"district": "Şişli", "city": "Istanbul"}],
        "categories": ["Parks"],
    },
    {
        "name": "Istanbul General Infrastructure",
        "description": "General infrastructure issues for all of Istanbul",
        "districts": [
            {"district": "Fatih", "city": "Istanbul"},
            {"district": "Beyoğlu", "city": "Istanbul"},
            {"district": "Üsküdar", "city": "Istanbul"},
        ],
        "categories": ["Infrastructure", "Lighting"],
    },
    {
        "name": "European Side Traffic",
        "description": "European side traffic management",
        "districts": [
            {"district": "Bakırköy", "city": "Istanbul"},
            {"district": "Beşiktaş", "city": "Istanbul"},
            {"district": "Şişli", "city": "Istanbul"},
            {"district": "Beyoğlu", "city": "Istanbul"},
        ],
        "categories": ["Traffic"],
    },
]


async def seed_districts() -> None:
    """Seed districts for Istanbul."""
    async with async_session_maker() as session:
        # Get existing districts
        result = await session.execute(select(District))
        existing = {(d.name, d.city) for d in result.scalars().all()}

        # Collect all unique districts from team data
        all_districts = set()
        for team_data in SAMPLE_TEAMS:
            for dist in team_data["districts"]:
                all_districts.add((dist["district"], dist["city"]))

        # Add new districts
        added_count = 0
        for district_name, city in all_districts:
            if (district_name, city) not in existing:
                district = District(name=district_name, city=city)
                session.add(district)
                added_count += 1
                logger.info(f"Created district: {district_name}, {city}")

        if added_count > 0:
            await session.commit()
            logger.info(f"Successfully created {added_count} districts")
        else:
            logger.info("All districts already exist")


async def seed_teams() -> None:
    """Seed teams with district and category assignments."""
    async with async_session_maker() as session:
        # First, ensure districts exist
        await seed_districts()
        
        # Get all categories for mapping
        result = await session.execute(select(Category))
        categories = {c.name: c for c in result.scalars().all()}
        
        if not categories:
            logger.warning("No categories found. Please run seed.py first!")
            return

        # Get all districts for mapping
        result = await session.execute(select(District))
        districts = {(d.name, d.city): d for d in result.scalars().all()}

        # Check existing teams
        result = await session.execute(select(Team))
        existing_teams = {t.name for t in result.scalars().all()}

        created_count = 0
        for team_data in SAMPLE_TEAMS:
            if team_data["name"] in existing_teams:
                logger.info(f"Team already exists: {team_data['name']}")
                continue

            # Create team
            team = Team(
                name=team_data["name"],
                description=team_data["description"],
            )
            session.add(team)
            await session.flush()  # Flush to get team.id

            # Add district assignments
            for district_data in team_data["districts"]:
                district_key = (district_data["district"], district_data["city"])
                district = districts.get(district_key)
                if district:
                    team_district = TeamDistrict(
                        team_id=team.id,
                        district_id=district.id,
                    )
                    session.add(team_district)
                else:
                    logger.warning(f"District not found: {district_key}")

            # Add category assignments
            for category_name in team_data["categories"]:
                category = categories.get(category_name)
                if category:
                    team_category = TeamCategory(
                        team_id=team.id,
                        category_id=category.id,
                    )
                    session.add(team_category)
                else:
                    logger.warning(f"Category not found: {category_name}")

            created_count += 1
            logger.info(
                f"Created team: {team_data['name']} "
                f"({len(team_data['districts'])} districts, "
                f"{len(team_data['categories'])} categories)"
            )

        if created_count > 0:
            await session.commit()
            logger.info(f"Successfully created {created_count} teams")
        else:
            logger.info("All teams already exist")


async def main() -> None:
    """Main seed function."""
    logger.info("Starting team seeding...")
    await seed_teams()
    logger.info("Team seeding completed!")


if __name__ == "__main__":
    asyncio.run(main())

