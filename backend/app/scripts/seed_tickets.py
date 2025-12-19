"""Seed script for test tickets - creates 20 tickets from 4 different users.

Run with: docker exec sosoft-backend python -m app.scripts.seed_tickets
"""

import asyncio
import logging
import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.database import async_session_maker
from app.models.category import Category
from app.models.ticket import Location, StatusLog, Ticket, TicketFollower, TicketStatus
from app.models.user import User, UserRole

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample ticket data
TICKET_TITLES = [
    "Broken sidewalk on Main Street",
    "Pothole on Oak Avenue causing damage",
    "Street light not working at Park Road",
    "Garbage bin overflowing in residential area",
    "Damaged traffic sign at intersection",
    "Flooding issue after heavy rain",
    "Tree branch blocking pedestrian path",
    "Graffiti on public building wall",
    "Broken bench in city park",
    "Noise complaint from construction site",
    "Sewer drain clogged causing odor",
    "Missing manhole cover on side street",
    "Damaged fence around playground",
    "Illegal parking blocking fire hydrant",
    "Broken glass on playground surface",
    "Water leak from fire hydrant",
    "Overgrown vegetation blocking view",
    "Damaged crosswalk paint",
    "Broken gate at community center",
    "Litter accumulation in public square",
]

TICKET_DESCRIPTIONS = [
    "The sidewalk has large cracks and is unsafe for pedestrians, especially elderly residents.",
    "This pothole has been getting worse and damaged my car's tire. Needs urgent repair.",
    "The street light has been out for over a week, making it unsafe at night.",
    "Garbage bin has been overflowing for days, attracting pests and creating health hazard.",
    "The stop sign is bent and hard to see, creating traffic safety concerns.",
    "Water accumulates here after every rain, making the road impassable.",
    "Large branch fell from tree and is blocking the entire sidewalk.",
    "Graffiti appeared overnight on the community center wall.",
    "One of the park benches is completely broken and unusable.",
    "Construction work continues late into the night, disturbing residents.",
    "Sewer drain is completely blocked and emitting foul odor.",
    "Manhole cover is missing, creating dangerous hazard for vehicles.",
    "Fence around playground has broken sections where children could get hurt.",
    "Cars are parking illegally and blocking access to fire hydrant.",
    "Broken glass scattered on playground surface, dangerous for children.",
    "Fire hydrant is leaking water continuously, wasting resources.",
    "Vegetation has grown so much it blocks visibility at intersection.",
    "Crosswalk paint has faded completely, making it hard to see.",
    "Gate at community center is broken and won't close properly.",
    "Public square has accumulated litter and needs cleaning.",
]

# Istanbul coordinates (for realistic locations)
ISTANBUL_DISTRICTS = [
    {"name": "Kadıköy", "lat": 40.9819, "lon": 29.0216},
    {"name": "Beşiktaş", "lat": 41.0431, "lon": 29.0075},
    {"name": "Şişli", "lat": 41.0602, "lon": 28.9874},
    {"name": "Beyoğlu", "lat": 41.0369, "lon": 28.9784},
    {"name": "Üsküdar", "lat": 41.0214, "lon": 29.0097},
    {"name": "Bakırköy", "lat": 40.9833, "lon": 28.8564},
]

STATUSES = [
    TicketStatus.NEW,
    TicketStatus.IN_PROGRESS,
    TicketStatus.RESOLVED,
    TicketStatus.CLOSED,
]


async def create_test_users() -> list[User]:
    """Create 4 test citizen users if they don't exist."""
    async with async_session_maker() as session:
        test_users_data = [
            {
                "name": "Ahmet Yılmaz",
                "email": "ahmet@example.com",
                "phone_number": "+905551111111",
            },
            {
                "name": "Ayşe Demir",
                "email": "ayse@example.com",
                "phone_number": "+905552222222",
            },
            {
                "name": "Mehmet Kaya",
                "email": "mehmet@example.com",
                "phone_number": "+905553333333",
            },
            {
                "name": "Fatma Şahin",
                "email": "fatma@example.com",
                "phone_number": "+905554444444",
            },
        ]

        # Check existing users
        result = await session.execute(select(User))
        existing_emails = {u.email for u in result.scalars().all()}

        created_users = []
        for user_data in test_users_data:
            if user_data["email"] not in existing_emails:
                from app.core.security import hash_password

                user = User(
                    name=user_data["name"],
                    email=user_data["email"],
                    phone_number=user_data["phone_number"],
                    password_hash=hash_password("test123!"),
                    role=UserRole.CITIZEN,
                    is_verified=True,
                    is_active=True,
                )
                session.add(user)
                created_users.append(user)
                logger.info(f"Created test user: {user_data['name']}")
            else:
                # Get existing user
                result = await session.execute(
                    select(User).where(User.email == user_data["email"])
                )
                user = result.scalar_one()
                created_users.append(user)

        await session.commit()

        # Refresh to get IDs
        for user in created_users:
            await session.refresh(user)

        return created_users


async def seed_tickets() -> None:
    """Create 20 test tickets from 4 different users."""
    logger.info("Starting ticket seed...")

    # Get or create test users
    users = await create_test_users()
    if len(users) < 4:
        logger.error("Failed to get/create 4 test users")
        return

    # Get categories
    async with async_session_maker() as session:
        result = await session.execute(select(Category).where(Category.is_active == True))
        categories = result.scalars().all()
        if not categories:
            logger.error("No categories found. Run seed.py first!")
            return

        # Create 20 tickets
        created_count = 0
        for i in range(20):
            # Random user (distribute evenly)
            user = users[i % 4]

            # Random category
            category = random.choice(categories)

            # Random district
            district = random.choice(ISTANBUL_DISTRICTS)
            # Add small random offset for variety
            lat = district["lat"] + random.uniform(-0.01, 0.01)
            lon = district["lon"] + random.uniform(-0.01, 0.01)

            # Random title and description
            title = TICKET_TITLES[i % len(TICKET_TITLES)]
            description = TICKET_DESCRIPTIONS[i % len(TICKET_DESCRIPTIONS)]

            # Random status (weighted towards NEW and IN_PROGRESS)
            status = random.choices(
                STATUSES,
                weights=[40, 30, 20, 10],  # More NEW tickets
            )[0]

            # Create location
            location = Location(
                latitude=lat,
                longitude=lon,
                address=f"{district['name']} District, Istanbul",
                district=district["name"],
                city="Istanbul",
                coordinates=f"POINT({lon} {lat})",
            )
            session.add(location)
            await session.flush()

            # Create ticket
            ticket = Ticket(
                title=title,
                description=description,
                category_id=category.id,
                location_id=location.id,
                reporter_id=user.id,
                status=status,
            )

            # Set resolved_at if status is RESOLVED or CLOSED
            if status in (TicketStatus.RESOLVED, TicketStatus.CLOSED):
                days_ago = random.randint(1, 30)
                ticket.resolved_at = datetime.now(timezone.utc) - timedelta(days=days_ago)

            session.add(ticket)
            await session.flush()

            # Auto-follow
            follower = TicketFollower(
                ticket_id=ticket.id,
                user_id=user.id,
            )
            session.add(follower)

            # Create initial status log
            status_log = StatusLog(
                ticket_id=ticket.id,
                old_status=None,
                new_status=status.value,
                changed_by_id=user.id,
            )
            session.add(status_log)

            created_count += 1
            logger.info(
                f"Created ticket #{created_count}: '{title}' by {user.name} ({status.value})"
            )

        await session.commit()
        logger.info(f"Successfully created {created_count} test tickets!")


async def main() -> None:
    """Main function."""
    try:
        await seed_tickets()
    except Exception as e:
        logger.error(f"Error seeding tickets: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())

