"""Seed script for comprehensive test data.

Creates tickets, feedback, escalations, and logs with realistic history and team assignments.
Run with: uv run python -m app.scripts.seed_tickets
"""

import asyncio
import logging
import random
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import async_session_maker
from app.core.security import hash_password
from app.models.category import Category
from app.models.ticket import Location, StatusLog, Ticket, TicketStatus
from app.models.user import User, UserRole
from app.models.team import Team, TeamDistrict
from app.models.feedback import Feedback
from app.models.escalation import EscalationRequest, EscalationStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
NUM_TICKETS = 250
DAYS_HISTORY = 90

# Sample Data
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
    "Stray dogs acting aggressively",
    "Park lights flickering at night",
    "Illegal dumping in empty lot",
    "Traffic signal stuck on red",
    "Bus stop shelter glass shattered",
]

FEEDBACK_COMMENTS = [
    "Thank you for the quick fix!",
    "Took longer than expected but job is done.",
    "Very satisfied with the service.",
    "The issue is resolved but left a mess behind.",
    "Excellent work, team was very professional.",
    "Still waiting for a permanent solution.",
    "Great response time!",
    "Could be better.",
    "Appreciate the help.",
    "Completely satisfied.",
]

ESCALATION_REASONS = [
    "Issue recurring despite previous fix",
    "Safety hazard requiring immediate attention",
    "No action taken for 2 weeks",
    "Incomplete resolution provided",
    "Citizen specifically requested manager review",
]

# Istanbul coordinates
ISTANBUL_DISTRICTS = [
    {"name": "Kadıköy", "lat": 40.9819, "lon": 29.0216},
    {"name": "Beşiktaş", "lat": 41.0431, "lon": 29.0075},
    {"name": "Şişli", "lat": 41.0602, "lon": 28.9874},
    {"name": "Beyoğlu", "lat": 41.0369, "lon": 28.9784},
    {"name": "Üsküdar", "lat": 41.0214, "lon": 29.0097},
    {"name": "Bakırköy", "lat": 40.9833, "lon": 28.8564},
    {"name": "Fatih", "lat": 41.0082, "lon": 28.9784},
]


async def create_users(role: UserRole, count: int, prefix: str, team_id: uuid.UUID | None = None) -> list[User]:
    """Create test users with specific role."""
    logger.info(f"Creating {count} users with role {role} (Team: {team_id})")
    async with async_session_maker() as session:
        created_users = []
        for i in range(count):
            email = f"{prefix}{i+1}@example.com"
            
            # Check exist
            existing_user = await session.scalar(select(User).where(User.email == email))
            if existing_user:
                # Update team if needed
                if team_id and existing_user.team_id != team_id:
                    existing_user.team_id = team_id
                    session.add(existing_user)
                created_users.append(existing_user)
                continue

            user = User(
                name=f"{prefix.capitalize()} User {i+1}",
                email=email,
                phone_number=f"+90555{str(i).zfill(3)}{str(random.randint(1000,9999))}", # Unique-ish phone
                password_hash=hash_password("test123!"),
                role=role,
                is_verified=True,
                is_active=True,
                team_id=team_id
            )
            session.add(user)
            created_users.append(user)
        
        await session.commit()
        logger.info("Users committed.")
        return created_users

async def seed_tickets() -> None:
    logger.info("Starting comprehensive data seed...")

    # 1. Get Teams First (for assignment)
    async with async_session_maker() as session:
        result = await session.execute(
            select(Team)
            .options(
                selectinload(Team.team_categories),
                selectinload(Team.team_districts).selectinload(TeamDistrict.district)
            )
        )
        teams = result.scalars().all()
        
        result = await session.execute(select(Category))
        categories = result.scalars().all()

    if not categories or not teams:
        logger.error("Missing categories or teams. Run seed_teams.py first.")
        return

    # 2. Setup Users with Teams
    # Distribute staff across teams
    citizens = await create_users(UserRole.CITIZEN, 10, "citizen")
    
    support_staff = []
    managers = []
    
    # Create support staff for each team
    for i, team in enumerate(teams):
        # 1-2 support per team
        s_users = await create_users(UserRole.SUPPORT, 2, f"support_{team.name.lower().replace(' ', '_')}", team_id=team.id)
        support_staff.extend(s_users)
        
        # 1 manager per team
        m_users = await create_users(UserRole.MANAGER, 1, f"manager_{team.name.lower().replace(' ', '_')}", team_id=team.id)
        managers.extend(m_users)
    
    all_staff = support_staff + managers

    # 3. Create Logs & Data
    count = 0
    logger.info(f"Generating {NUM_TICKETS} tickets...")

    # Pre-create some common locations (hotspots) to simulate real-world clustering
    location_pool = []

    async with async_session_maker() as session:
        # Create ~50 common locations across all districts
        logger.info("Creating common location hotspots...")
        for _ in range(50):
            district_info = random.choice(ISTANBUL_DISTRICTS)
            lat = district_info["lat"] + random.uniform(-0.005, 0.005)
            lon = district_info["lon"] + random.uniform(-0.005, 0.005)
            location = Location(
                latitude=lat,
                longitude=lon,
                address=f"{district_info['name']} District, Istanbul",
                district=district_info['name'],
                city="Istanbul",
                coordinates=f"POINT({lon} {lat})",
            )
            session.add(location)
            location_pool.append((location, district_info['name']))

        await session.flush()
        logger.info(f"Created {len(location_pool)} common locations")

        for i in range(NUM_TICKETS):
            reporter = random.choice(citizens)
            category = random.choice(categories)
            district_info = random.choice(ISTANBUL_DISTRICTS)

            # Date simulation with higher density in recent days
            rand_date = random.random()
            if rand_date < 0.40: # 40% in last 7 days
                days_ago = random.randint(0, 7)
            elif rand_date < 0.80: # 40% in last 8-30 days
                days_ago = random.randint(8, 30)
            else: # 20% in last 31-90 days
                days_ago = random.randint(31, DAYS_HISTORY)

            created_at = datetime.now(timezone.utc) - timedelta(days=days_ago)

            # Assign Team Logic (Simple matching)
            assigned_team = None
            candidates = []
            for team in teams:
                # Check category match
                cat_match = any(tc.category_id == category.id for tc in team.team_categories)
                # Check district match
                dist_match = any(
                    td.district.name == district_info["name"]
                    for td in team.team_districts
                    if td.district # Ensure district is loaded and not None
                )

                if cat_match and dist_match:
                    candidates.append(team)

            # Fallback: just category match
            if not candidates:
                candidates = [t for t in teams if any(tc.category_id == category.id for tc in t.team_categories)]

            # Fallback: any team
            if not candidates:
                candidates = teams

            assigned_team = random.choice(candidates)

            # Location: 60% chance to use existing hotspot, 40% chance to create new
            if random.random() < 0.6 and location_pool:
                # Try to find a location in the same district
                same_district_locs = [loc for loc, dist in location_pool if dist == district_info['name']]
                if same_district_locs:
                    location = random.choice(same_district_locs)
                else:
                    # Fallback to any location
                    location, _ = random.choice(location_pool)
            else:
                # Create new unique location
                lat = district_info["lat"] + random.uniform(-0.005, 0.005)
                lon = district_info["lon"] + random.uniform(-0.005, 0.005)
                location = Location(
                    latitude=lat,
                    longitude=lon,
                    address=f"{district_info['name']} District, Istanbul",
                    district=district_info['name'],
                    city="Istanbul",
                    coordinates=f"POINT({lon} {lat})",
                )
                session.add(location)
                await session.flush()
                location_pool.append((location, district_info['name']))

            # Determine status
            rand_val = random.random()
            if rand_val < 0.15:
                status = TicketStatus.NEW
            elif rand_val < 0.4:
                status = TicketStatus.IN_PROGRESS
            elif rand_val < 0.55:
                status = TicketStatus.ESCALATED
            else:
                status = TicketStatus.RESOLVED # Mostly resolved for data density

            # Create Ticket
            ticket = Ticket(
                title=random.choice(TICKET_TITLES),
                description=f"Automated test ticket generated for {category.name} in {district_info['name']}.",
                category_id=category.id,
                location_id=location.id,
                reporter_id=reporter.id,
                status=status,
                created_at=created_at,
                team_id=assigned_team.id,
            )
            session.add(ticket)
            await session.flush()

            # 4. Create History (Logs)
            # Log 1: Created
            log1 = StatusLog(
                ticket_id=ticket.id,
                old_status=None,
                new_status=TicketStatus.NEW,
                changed_by_id=reporter.id,
                created_at=created_at
            )
            session.add(log1)

            # If progressed
            if status != TicketStatus.NEW:
                # Pick a staff member
                staff = random.choice(all_staff)

                # Time gap
                hours_later = random.randint(1, 48)
                in_progress_at = created_at + timedelta(hours=hours_later)

                # Update ticket timestamp (simulating update time)
                if status == TicketStatus.IN_PROGRESS:
                    ticket.updated_at = in_progress_at

                log2 = StatusLog(
                    ticket_id=ticket.id,
                    old_status=TicketStatus.NEW,
                    new_status=TicketStatus.IN_PROGRESS,
                    changed_by_id=staff.id,
                    created_at=in_progress_at
                )
                session.add(log2)

                # If resolved
                if status == TicketStatus.RESOLVED:
                    resolve_hours = random.randint(2, 72)
                    resolved_at = in_progress_at + timedelta(hours=resolve_hours)
                    ticket.resolved_at = resolved_at
                    ticket.updated_at = resolved_at

                    log3 = StatusLog(
                        ticket_id=ticket.id,
                        old_status=TicketStatus.IN_PROGRESS,
                        new_status=TicketStatus.RESOLVED,
                        changed_by_id=staff.id,
                        created_at=resolved_at
                    )
                    session.add(log3)

                    # 5. Add Feedback (for resolved tickets)
                    if random.random() < 0.85:
                        feedback = Feedback(
                            ticket_id=ticket.id,
                            user_id=reporter.id,
                            rating=random.choices([1,2,3,4,5], weights=[5,10,20,40,25])[0],
                            comment=random.choice(FEEDBACK_COMMENTS),
                            created_at=resolved_at + timedelta(days=random.randint(1, 3))
                        )
                        session.add(feedback)

                # If escalated
                if status == TicketStatus.ESCALATED:
                    # First go to in_progress
                    if ticket.updated_at is None:
                         ticket.updated_at = in_progress_at

                    esc_at = in_progress_at + timedelta(hours=random.randint(4, 24))
                    ticket.updated_at = esc_at

                    log4 = StatusLog(
                        ticket_id=ticket.id,
                        old_status=TicketStatus.IN_PROGRESS,
                        new_status=TicketStatus.ESCALATED,
                        changed_by_id=staff.id,
                        created_at=esc_at
                    )
                    session.add(log4)

                    # Create the escalation request
                    escalation = EscalationRequest(
                        ticket_id=ticket.id,
                        requester_id=staff.id,
                        reason=random.choice(ESCALATION_REASONS),
                        status=EscalationStatus.PENDING,
                        created_at=esc_at
                    )
                    # Sometimes approve/reject it
                    if random.random() < 0.5: # 50% are processed
                        reviewer = random.choice(managers)
                        escalation.reviewer_id = reviewer.id
                        escalation.status = random.choice([EscalationStatus.APPROVED, EscalationStatus.REJECTED])
                        escalation.reviewed_at = escalation.created_at + timedelta(hours=random.randint(1, 24))
                        escalation.review_comment = "Processed via automated flow."

                    session.add(escalation)

            count += 1
            if count % 10 == 0:
                logger.info(f"Generated {count} tickets...")

        await session.commit()
        logger.info(f"Successfully generated {count} tickets with full history!")

async def main():
    try:
        await seed_tickets()
    except Exception as e:
        logger.error(f"Seeding failed: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
