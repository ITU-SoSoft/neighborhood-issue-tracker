"""Create test tickets with varied locations for heatmap visualization.

Run with: docker exec sosoft-backend python -m app.scripts.create_test_tickets
"""

import asyncio
import logging
import random

from sqlalchemy import select

from app.database import async_session_maker
from app.models.category import Category
from app.models.ticket import Location, StatusLog, Ticket, TicketStatus, TicketFollower
from app.models.user import User, UserRole

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Istanbul coordinates with some variation for different neighborhoods
# Creating hotspot areas with multiple base locations for better clustering
ISTANBUL_LOCATIONS = [
    # Kadıköy area - HOTSPOT (high density)
    {"lat": 40.9929, "lng": 29.0253, "address": "Kadıköy Center", "district": "Kadıköy", "weight": 15},
    {"lat": 40.9889, "lng": 29.0203, "address": "Moda, Kadıköy", "district": "Kadıköy", "weight": 12},
    {"lat": 41.0029, "lng": 29.0353, "address": "Acıbadem, Kadıköy", "district": "Kadıköy", "weight": 10},
    {"lat": 40.9989, "lng": 29.0303, "address": "Fenerbahçe, Kadıköy", "district": "Kadıköy", "weight": 8},
    {"lat": 40.9869, "lng": 29.0283, "address": "Caferağa, Kadıköy", "district": "Kadıköy", "weight": 7},

    # Beşiktaş area - HOTSPOT (high density)
    {"lat": 41.0422, "lng": 29.0084, "address": "Beşiktaş Center", "district": "Beşiktaş", "weight": 14},
    {"lat": 41.0522, "lng": 29.0184, "address": "Ortaköy, Beşiktaş", "district": "Beşiktaş", "weight": 11},
    {"lat": 41.0482, "lng": 29.0134, "address": "Arnavutköy, Beşiktaş", "district": "Beşiktaş", "weight": 9},
    {"lat": 41.0382, "lng": 29.0034, "address": "Abbasağa, Beşiktaş", "district": "Beşiktaş", "weight": 8},

    # Şişli area - HOTSPOT (high density)
    {"lat": 41.0602, "lng": 28.9866, "address": "Şişli Center", "district": "Şişli", "weight": 13},
    {"lat": 41.0682, "lng": 28.9966, "address": "Mecidiyeköy, Şişli", "district": "Şişli", "weight": 12},
    {"lat": 41.0552, "lng": 28.9916, "address": "Osmanbey, Şişli", "district": "Şişli", "weight": 10},
    {"lat": 41.0632, "lng": 28.9816, "address": "Nişantaşı, Şişli", "district": "Şişli", "weight": 9},

    # Fatih (old city) area - MEDIUM HOTSPOT
    {"lat": 41.0086, "lng": 28.9802, "address": "Sultanahmet, Fatih", "district": "Fatih", "weight": 8},
    {"lat": 41.0186, "lng": 28.9702, "address": "Eminönü, Fatih", "district": "Fatih", "weight": 7},
    {"lat": 41.0136, "lng": 28.9752, "address": "Sirkeci, Fatih", "district": "Fatih", "weight": 6},
    {"lat": 41.0086, "lng": 28.9652, "address": "Aksaray, Fatih", "district": "Fatih", "weight": 5},

    # Bakırköy area - MEDIUM DENSITY
    {"lat": 40.9778, "lng": 28.8668, "address": "Bakırköy Center", "district": "Bakırköy", "weight": 7},
    {"lat": 40.9828, "lng": 28.8718, "address": "Ataköy, Bakırköy", "district": "Bakırköy", "weight": 6},
    {"lat": 40.9728, "lng": 28.8618, "address": "Yeşilköy, Bakırköy", "district": "Bakırköy", "weight": 5},

    # Üsküdar area (Asian side) - HOTSPOT
    {"lat": 41.0225, "lng": 29.0152, "address": "Üsküdar Center", "district": "Üsküdar", "weight": 11},
    {"lat": 41.0325, "lng": 29.0252, "address": "Kısıklı, Üsküdar", "district": "Üsküdar", "weight": 9},
    {"lat": 41.0275, "lng": 29.0202, "address": "Altunizade, Üsküdar", "district": "Üsküdar", "weight": 8},
    {"lat": 41.0175, "lng": 29.0102, "address": "Salacak, Üsküdar", "district": "Üsküdar", "weight": 7},

    # Sarıyer area (north) - LOW DENSITY
    {"lat": 41.1602, "lng": 29.0466, "address": "Sarıyer Center", "district": "Sarıyer", "weight": 4},
    {"lat": 41.1502, "lng": 29.0566, "address": "Tarabya, Sarıyer", "district": "Sarıyer", "weight": 3},

    # Beyoğlu area - VERY HIGH HOTSPOT
    {"lat": 41.0344, "lng": 28.9784, "address": "Taksim, Beyoğlu", "district": "Beyoğlu", "weight": 16},
    {"lat": 41.0294, "lng": 28.9734, "address": "İstiklal, Beyoğlu", "district": "Beyoğlu", "weight": 14},
    {"lat": 41.0244, "lng": 28.9684, "address": "Karaköy, Beyoğlu", "district": "Beyoğlu", "weight": 12},
    {"lat": 41.0394, "lng": 28.9834, "address": "Harbiye, Beyoğlu", "district": "Beyoğlu", "weight": 10},

    # Maltepe area (Asian side) - MEDIUM DENSITY
    {"lat": 40.9341, "lng": 29.1284, "address": "Maltepe Center", "district": "Maltepe", "weight": 6},
    {"lat": 40.9291, "lng": 29.1234, "address": "Bağlarbaşı, Maltepe", "district": "Maltepe", "weight": 5},

    # Kartal area (Asian side) - MEDIUM DENSITY
    {"lat": 40.8957, "lng": 29.1897, "address": "Kartal Center", "district": "Kartal", "weight": 6},
    {"lat": 40.9007, "lng": 29.1847, "address": "Soğanlık, Kartal", "district": "Kartal", "weight": 5},
]

TICKET_TITLES = [
    "Broken streetlight on main road",
    "Pothole on sidewalk needs repair",
    "Garbage collection missed",
    "Illegal parking blocking entrance",
    "Tree branches blocking traffic sign",
    "Park bench damaged",
    "Street sign missing",
    "Graffiti on public building",
    "Overflowing trash bin",
    "Broken water fountain in park",
    "Damaged pedestrian crossing",
    "Noise complaint - construction",
]

DESCRIPTIONS = [
    "Noticed this issue yesterday during evening hours. Requires immediate attention.",
    "This has been an ongoing problem for the past week. Community members are concerned.",
    "Multiple residents have reported this issue. Please investigate.",
    "Safety hazard that needs to be addressed as soon as possible.",
    "First noticed today. Would appreciate a quick resolution.",
    "This is affecting daily activities in the neighborhood.",
]


async def create_test_tickets(count: int = 300) -> None:
    """Create test tickets with weighted random locations in Istanbul.

    Uses location weights to create realistic clustering - high-weight areas
    get more tickets, creating visible hotspots on the heatmap.
    """
    async with async_session_maker() as session:
        # Get all categories
        category_result = await session.execute(
            select(Category).where(Category.is_active)
        )
        categories = list(category_result.scalars().all())

        if not categories:
            logger.error("No categories found. Run seed script first.")
            return

        # Get a citizen user to be the reporter
        user_result = await session.execute(
            select(User).where(
                User.deleted_at.is_(None),
                User.role == UserRole.CITIZEN,
            )
        )
        reporter = user_result.scalar_one_or_none()

        if not reporter:
            # Create a test citizen if none exists
            from app.core.security import hash_password
            reporter = User(
                name="Test Citizen",
                email="citizen@test.com",
                phone_number="+905009999999",
                password_hash=hash_password("test123!"),
                role=UserRole.CITIZEN,
                is_verified=True,
            )
            session.add(reporter)
            await session.flush()

        created_count = 0
        # More in_progress tickets for better heatmap visualization
        statuses = [
            TicketStatus.IN_PROGRESS,  # 70% in_progress
            TicketStatus.IN_PROGRESS,
            TicketStatus.IN_PROGRESS,
            TicketStatus.IN_PROGRESS,
            TicketStatus.IN_PROGRESS,
            TicketStatus.IN_PROGRESS,
            TicketStatus.IN_PROGRESS,
            TicketStatus.NEW,  # 20% new
            TicketStatus.NEW,
            TicketStatus.RESOLVED,  # 10% resolved
        ]

        # Create weighted location list for realistic clustering
        weighted_locations = []
        for loc in ISTANBUL_LOCATIONS:
            # Add each location multiple times based on its weight
            weighted_locations.extend([loc] * loc["weight"])

        logger.info(f"Creating {count} tickets across {len(ISTANBUL_LOCATIONS)} locations with clustering...")

        for i in range(count):
            # Select location using weighted random choice
            loc_data = random.choice(weighted_locations)

            # Add random variation to coordinates
            # Smaller variation (±0.003 degrees ~ ±300m) for tighter clusters
            lat_variation = random.uniform(-0.003, 0.003)
            lng_variation = random.uniform(-0.003, 0.003)

            location = Location(
                latitude=loc_data["lat"] + lat_variation,
                longitude=loc_data["lng"] + lng_variation,
                address=loc_data["address"],
                district=loc_data["district"],
                city="Istanbul",
                coordinates=f"POINT({loc_data['lng'] + lng_variation} {loc_data['lat'] + lat_variation})",
            )
            session.add(location)
            await session.flush()

            # Create ticket
            status = random.choice(statuses)
            ticket = Ticket(
                title=random.choice(TICKET_TITLES),
                description=random.choice(DESCRIPTIONS),
                category_id=random.choice(categories).id,
                location_id=location.id,
                reporter_id=reporter.id,
                status=status,
            )
            session.add(ticket)
            await session.flush()

            # Auto-follow the ticket
            follower = TicketFollower(
                ticket_id=ticket.id,
                user_id=reporter.id,
            )
            session.add(follower)

            # Create initial status log
            status_log = StatusLog(
                ticket_id=ticket.id,
                old_status=None,
                new_status=status.value,
                changed_by_id=reporter.id,
            )
            session.add(status_log)

            created_count += 1

            # Log progress every 50 tickets
            if created_count % 50 == 0:
                logger.info(f"Progress: {created_count}/{count} tickets created...")

        await session.commit()
        logger.info(f"✓ Successfully created {created_count} test tickets across Istanbul!")
        logger.info(f"  - {len([s for s in statuses if s == TicketStatus.IN_PROGRESS])*10}% in_progress (visible on heatmap)")
        logger.info(f"  - {len([s for s in statuses if s == TicketStatus.NEW])*10}% new")
        logger.info(f"  - {len([s for s in statuses if s == TicketStatus.RESOLVED])*10}% resolved")


async def main() -> None:
    """Main function."""
    logger.info("=" * 70)
    logger.info("Creating test tickets for heatmap visualization...")
    logger.info("This will generate 300 tickets with realistic clustering")
    logger.info("=" * 70)
    await create_test_tickets(count=300)
    logger.info("=" * 70)
    logger.info("✓ Test ticket creation completed!")
    logger.info("  Refresh your dashboard to see the improved heatmap!")
    logger.info("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
