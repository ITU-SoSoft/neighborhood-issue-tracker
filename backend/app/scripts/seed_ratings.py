"""Seed script for testing average rating calculations.

Creates resolved tickets with various ratings to test average rating analytics.
Run with: uv run python -m app.scripts.seed_ratings
"""

import asyncio
import logging
import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import async_session_maker
from app.models.category import Category
from app.models.feedback import Feedback
from app.models.ticket import Location, Ticket, TicketStatus
from app.models.user import User, UserRole
from app.models.team import Team, TeamDistrict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rating distributions for different scenarios
RATING_SCENARIOS = {
    "excellent": [5, 5, 5, 4, 4, 5, 5, 4, 5, 4],  # Average ~4.6
    "good": [4, 4, 3, 4, 5, 3, 4, 4, 3, 4],  # Average ~3.8
    "average": [3, 3, 3, 4, 2, 3, 4, 3, 2, 3],  # Average ~3.0
    "poor": [2, 2, 1, 3, 2, 1, 2, 3, 1, 2],  # Average ~1.9
    "mixed": [5, 1, 4, 2, 5, 1, 4, 3, 5, 2],  # Average ~3.2
}

FEEDBACK_COMMENTS = {
    5: [
        "Excellent service! Very satisfied.",
        "Outstanding work, thank you!",
        "Perfect resolution, highly recommend!",
        "Exceeded expectations, great job!",
    ],
    4: [
        "Good service, satisfied with the result.",
        "Well done, minor issues but overall good.",
        "Professional and efficient.",
        "Good work, thank you.",
    ],
    3: [
        "Average service, could be better.",
        "It's okay, nothing special.",
        "Met expectations but nothing more.",
        "Acceptable but room for improvement.",
    ],
    2: [
        "Below expectations, needs improvement.",
        "Not satisfied, took too long.",
        "Could have been better.",
        "Disappointed with the service.",
    ],
    1: [
        "Very poor service, not recommended.",
        "Terrible experience, very disappointed.",
        "Worst service I've ever received.",
        "Completely unsatisfied.",
    ],
}

# Istanbul coordinates
ISTANBUL_DISTRICTS = [
    {"name": "Kadıköy", "lat": 40.9819, "lon": 29.0216},
    {"name": "Beşiktaş", "lat": 41.0431, "lon": 29.0075},
    {"name": "Şişli", "lat": 41.0602, "lon": 28.9874},
    {"name": "Beyoğlu", "lat": 41.0369, "lon": 28.9784},
    {"name": "Üsküdar", "lat": 41.0214, "lon": 29.0097},
]


async def seed_ratings() -> None:
    """Create resolved tickets with various ratings for testing average rating calculations."""
    logger.info("Starting rating seed...")

    async with async_session_maker() as session:
        # Get existing data
        result = await session.execute(
            select(Team).options(
                selectinload(Team.team_categories),
                selectinload(Team.team_districts).selectinload(TeamDistrict.district),
            )
        )
        teams = result.scalars().all()

        result = await session.execute(select(Category))
        categories = result.scalars().all()

        result = await session.execute(
            select(User).where(User.role == UserRole.CITIZEN)
        )
        citizens = result.scalars().all()

        if not teams or not categories or not citizens:
            logger.error(
                "Missing required data. Please ensure teams, categories, and citizen users exist."
            )
            return

        # Create a citizen user if none exist
        if not citizens:
            logger.info("Creating test citizen user...")
            from app.core.security import hash_password

            citizen = User(
                name="Test Citizen",
                email="test_citizen@example.com",
                phone_number="+905551234567",
                password_hash=hash_password("test123!"),
                role=UserRole.CITIZEN,
                is_verified=True,
                is_active=True,
            )
            session.add(citizen)
            await session.flush()
            citizens = [citizen]

        logger.info(f"Found {len(teams)} teams, {len(categories)} categories, {len(citizens)} citizens")

        # Create tickets with different rating scenarios
        tickets_created = 0
        feedbacks_created = 0

        # Create tickets for each scenario
        for scenario_name, ratings in RATING_SCENARIOS.items():
            logger.info(f"Creating tickets for scenario: {scenario_name} (avg rating: {sum(ratings)/len(ratings):.2f})")

            # Create tickets for each rating in the scenario
            for rating in ratings:
                # Select random team, category, and citizen
                team = random.choice(teams)
                category = random.choice(categories)
                reporter = random.choice(citizens)

                # Get a district for the team or use a random one
                district_info = random.choice(ISTANBUL_DISTRICTS)
                if team.team_districts:
                    # Try to use team's district
                    team_district = random.choice(team.team_districts)
                    if team_district.district:
                        district_name = team_district.district.name
                        # Find matching district info
                        district_info = next(
                            (d for d in ISTANBUL_DISTRICTS if d["name"] == district_name),
                            district_info,
                        )

                # Create location
                lat = district_info["lat"] + random.uniform(-0.005, 0.005)
                lon = district_info["lon"] + random.uniform(-0.005, 0.005)
                location = Location(
                    latitude=lat,
                    longitude=lon,
                    address=f"{district_info['name']} District, Istanbul",
                    district=district_info["name"],
                    city="Istanbul",
                    coordinates=f"POINT({lon} {lat})",
                )
                session.add(location)
                await session.flush()

                # Create ticket with resolved status
                # Spread tickets over last 30 days
                days_ago = random.randint(0, 30)
                created_at = datetime.now(timezone.utc) - timedelta(days=days_ago)
                resolved_at = created_at + timedelta(
                    hours=random.randint(2, 72)
                )  # Resolved within 2-72 hours

                ticket = Ticket(
                    title=f"Test ticket for rating scenario: {scenario_name}",
                    description=f"Automated test ticket for {scenario_name} scenario with rating {rating}.",
                    category_id=category.id,
                    location_id=location.id,
                    reporter_id=reporter.id,
                    team_id=team.id,
                    status=TicketStatus.RESOLVED,
                    created_at=created_at,
                    resolved_at=resolved_at,
                    updated_at=resolved_at,
                )
                session.add(ticket)
                await session.flush()
                tickets_created += 1

                # Create feedback with the rating
                feedback = Feedback(
                    ticket_id=ticket.id,
                    user_id=reporter.id,
                    rating=rating,
                    comment=random.choice(FEEDBACK_COMMENTS[rating]),
                    created_at=resolved_at + timedelta(days=random.randint(1, 3)),
                )
                session.add(feedback)
                feedbacks_created += 1

        # Create additional tickets with specific rating distributions per category
        logger.info("Creating category-specific rating distributions...")
        for category in categories:
            # Create 10 tickets per category with varied ratings
            category_ratings = [5, 4, 3, 2, 1, 5, 4, 3, 4, 5]  # Average ~3.8
            for rating in category_ratings:
                team = random.choice(teams)
                reporter = random.choice(citizens)
                district_info = random.choice(ISTANBUL_DISTRICTS)

                lat = district_info["lat"] + random.uniform(-0.005, 0.005)
                lon = district_info["lon"] + random.uniform(-0.005, 0.005)
                location = Location(
                    latitude=lat,
                    longitude=lon,
                    address=f"{district_info['name']} District, Istanbul",
                    district=district_info["name"],
                    city="Istanbul",
                    coordinates=f"POINT({lon} {lat})",
                )
                session.add(location)
                await session.flush()

                days_ago = random.randint(0, 30)
                created_at = datetime.now(timezone.utc) - timedelta(days=days_ago)
                resolved_at = created_at + timedelta(hours=random.randint(2, 72))

                ticket = Ticket(
                    title=f"Category test ticket: {category.name}",
                    description=f"Test ticket for category {category.name} with rating {rating}.",
                    category_id=category.id,
                    location_id=location.id,
                    reporter_id=reporter.id,
                    team_id=team.id,
                    status=TicketStatus.RESOLVED,
                    created_at=created_at,
                    resolved_at=resolved_at,
                    updated_at=resolved_at,
                )
                session.add(ticket)
                await session.flush()
                tickets_created += 1

                feedback = Feedback(
                    ticket_id=ticket.id,
                    user_id=reporter.id,
                    rating=rating,
                    comment=random.choice(FEEDBACK_COMMENTS[rating]),
                    created_at=resolved_at + timedelta(days=random.randint(1, 3)),
                )
                session.add(feedback)
                feedbacks_created += 1

        # Create team-specific rating distributions
        logger.info("Creating team-specific rating distributions...")
        for team in teams[:5]:  # Limit to first 5 teams to avoid too many tickets
            # Create 8 tickets per team with varied ratings
            team_ratings = [5, 5, 4, 4, 3, 3, 2, 5]  # Average ~3.75
            for rating in team_ratings:
                category = random.choice(categories)
                reporter = random.choice(citizens)
                district_info = random.choice(ISTANBUL_DISTRICTS)

                lat = district_info["lat"] + random.uniform(-0.005, 0.005)
                lon = district_info["lon"] + random.uniform(-0.005, 0.005)
                location = Location(
                    latitude=lat,
                    longitude=lon,
                    address=f"{district_info['name']} District, Istanbul",
                    district=district_info["name"],
                    city="Istanbul",
                    coordinates=f"POINT({lon} {lat})",
                )
                session.add(location)
                await session.flush()

                days_ago = random.randint(0, 30)
                created_at = datetime.now(timezone.utc) - timedelta(days=days_ago)
                resolved_at = created_at + timedelta(hours=random.randint(2, 72))

                ticket = Ticket(
                    title=f"Team test ticket: {team.name}",
                    description=f"Test ticket for team {team.name} with rating {rating}.",
                    category_id=category.id,
                    location_id=location.id,
                    reporter_id=reporter.id,
                    team_id=team.id,
                    status=TicketStatus.RESOLVED,
                    created_at=created_at,
                    resolved_at=resolved_at,
                    updated_at=resolved_at,
                )
                session.add(ticket)
                await session.flush()
                tickets_created += 1

                feedback = Feedback(
                    ticket_id=ticket.id,
                    user_id=reporter.id,
                    rating=rating,
                    comment=random.choice(FEEDBACK_COMMENTS[rating]),
                    created_at=resolved_at + timedelta(days=random.randint(1, 3)),
                )
                session.add(feedback)
                feedbacks_created += 1

        await session.commit()

        logger.info("=" * 60)
        logger.info("✅ Rating seed complete!")
        logger.info(f"   Tickets created: {tickets_created}")
        logger.info(f"   Feedbacks created: {feedbacks_created}")
        logger.info("=" * 60)
        logger.info("\n📊 Rating Scenarios Created:")
        for scenario_name, ratings in RATING_SCENARIOS.items():
            avg = sum(ratings) / len(ratings)
            logger.info(f"   {scenario_name}: {len(ratings)} tickets, avg rating: {avg:.2f}")
        logger.info("=" * 60)


async def main():
    """Main entry point."""
    try:
        await seed_ratings()
    except Exception as e:
        logger.error(f"Seeding failed: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())

