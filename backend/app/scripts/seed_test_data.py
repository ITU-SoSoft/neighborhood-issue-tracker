"""Seed test data: 6 districts x 2 categories = 12 teams with 2 members each."""
import asyncio
import random
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.core.security import hash_password
from app.models.category import Category
from app.models.district import District
from app.models.team import Team, TeamCategory, TeamDistrict
from app.models.ticket import Ticket, TicketStatus, Location
from app.models.user import User, UserRole

# Test districts (6 districts)
TEST_DISTRICTS = [
    "Kadıköy",
    "Beşiktaş", 
    "Şişli",
    "Maltepe",
    "Kartal",
    "Pendik",
]

# Test categories (2 categories)
TEST_CATEGORIES = [
    "Traffic",
    "Infrastructure",
]

# Turkish first names and last names for random user generation
FIRST_NAMES = [
    "Ahmet", "Mehmet", "Ayşe", "Fatma", "Mustafa", "Emine", 
    "Ali", "Zeynep", "Hüseyin", "Elif", "Hasan", "Merve",
    "İbrahim", "Selin", "Yusuf", "Deniz", "Ömer", "Seda",
]

LAST_NAMES = [
    "Yılmaz", "Kaya", "Demir", "Şahin", "Çelik", "Yıldız",
    "Yıldırım", "Öztürk", "Aydın", "Özdemir", "Arslan", "Doğan",
    "Kılıç", "Aslan", "Çetin", "Koç", "Kurt", "Özkan",
]

# Ticket templates by category
TRAFFIC_ISSUES = [
    "Trafik ışığı arızalı",
    "Yol çökmesi var",
    "Kaldırım bozuk",
    "Yol çizgileri silinmiş",
    "Trafik levhası eksik",
    "Yolda büyük çukur var",
    "Kavşakta ışık çalışmıyor",
    "Yaya geçidi silinmiş",
    "Yol daraltma gerekli",
    "Hız kasis aşınmış",
]

INFRASTRUCTURE_ISSUES = [
    "Kanalizasyon tıkalı",
    "Su borusu patlamış",
    "Elektrik direği yıkılmış",
    "Yağmur suyu ızgarası kırık",
    "Altyapı çökmüş",
    "Kablo askıda",
    "Rögar kapağı eksik",
    "Baca temizlik gerekli",
    "Doğalgaz kokusu var",
    "Su kaçağı var",
]

DISTRICT_LOCATIONS = {
    "Kadıköy": [(40.9829, 29.0296), (40.9886, 29.0242), (40.9799, 29.0366)],
    "Beşiktaş": [(41.0422, 29.0096), (41.0486, 29.0000), (41.0375, 29.0150)],
    "Şişli": [(41.0602, 28.9870), (41.0550, 28.9920), (41.0650, 28.9800)],
    "Maltepe": [(40.9285, 29.1452), (40.9335, 29.1500), (40.9245, 29.1400)],
    "Kartal": [(40.9008, 29.1845), (40.9050, 29.1900), (40.8950, 29.1800)],
    "Pendik": [(40.8769, 29.2328), (40.8800, 29.2400), (40.8700, 29.2250)],
}


async def create_test_teams_and_users() -> None:
    """Create 12 teams (6 districts x 2 categories) with 2 support users each."""
    async with async_session_maker() as session:
        # Get categories
        result = await session.execute(select(Category))
        all_categories = {c.name: c for c in result.scalars().all()}
        
        # Get districts
        result = await session.execute(select(District))
        all_districts = {d.name: d for d in result.scalars().all()}
        
        # Verify we have the required categories
        missing_categories = set(TEST_CATEGORIES) - set(all_categories.keys())
        if missing_categories:
            print(f"❌ Missing categories: {missing_categories}")
            print("   Please ensure these categories exist in the database.")
            return
        
        # Verify we have the required districts
        missing_districts = set(TEST_DISTRICTS) - set(all_districts.keys())
        if missing_districts:
            print(f"❌ Missing districts: {missing_districts}")
            print("   Please ensure these districts exist in the database.")
            return
        
        teams_created = 0
        users_created = 0
        
        # Create teams for each district x category combination
        for district_name in TEST_DISTRICTS:
            for category_name in TEST_CATEGORIES:
                district = all_districts[district_name]
                category = all_categories[category_name]
                
                team_name = f"{district_name} {category_name} Team"
                
                # Check if team already exists
                result = await session.execute(
                    select(Team).where(Team.name == team_name)
                )
                existing_team = result.scalar_one_or_none()
                
                if existing_team:
                    print(f"⏭️  Team already exists: {team_name}")
                    team = existing_team
                else:
                    # Create team
                    team = Team(
                        name=team_name,
                        description=f"Handles {category_name.lower()} issues in {district_name}",
                    )
                    session.add(team)
                    await session.flush()
                    
                    # Add category
                    team_category = TeamCategory(
                        team_id=team.id,
                        category_id=category.id,
                    )
                    session.add(team_category)
                    
                    # Add district
                    team_district = TeamDistrict(
                        team_id=team.id,
                        district_id=district.id,
                    )
                    session.add(team_district)
                    
                    await session.commit()
                    teams_created += 1
                    print(f"✅ Created team: {team_name}")
                
                # Create 2 support users for this team
                for i in range(1, 3):
                    first_name = random.choice(FIRST_NAMES)
                    last_name = random.choice(LAST_NAMES)
                    username = f"{first_name.lower()}.{last_name.lower()}.{district_name.lower()[:3]}.{category_name.lower()[:3]}.{i}"
                    email = f"{username}@support.com"
                    phone = f"+9053{random.randint(10000000, 99999999)}"
                    
                    # Check if user already exists
                    result = await session.execute(
                        select(User).where(User.email == email)
                    )
                    if result.scalar_one_or_none():
                        print(f"   ⏭️  User already exists: {email}")
                        continue
                    
                    user = User(
                        name=f"{first_name} {last_name}",
                        email=email,
                        phone_number=phone,
                        password_hash=hash_password("test123!"),
                        role=UserRole.SUPPORT,
                        team_id=team.id,
                        is_verified=True,
                        is_active=True,
                    )
                    session.add(user)
                    users_created += 1
                    print(f"   ✅ Created user: {email} (Team: {team_name})")
        
        await session.commit()
        
        print("\n" + "="*60)
        print(f"✅ Test data creation complete!")
        print(f"   Teams created: {teams_created}")
        print(f"   Users created: {users_created}")
        print(f"   Total teams: {len(TEST_DISTRICTS) * len(TEST_CATEGORIES)} ({len(TEST_DISTRICTS)} districts x {len(TEST_CATEGORIES)} categories)")
        print(f"   Total users expected: {len(TEST_DISTRICTS) * len(TEST_CATEGORIES) * 2} (2 per team)")
        print("="*60)
        print("\n📋 Test Credentials:")
        print("   Any user: <email>@support.com")
        print("   Password: test123!")
        print("\n   Example: ahmet.yilmaz.kad.tra.1@support.com")
        print("="*60)


async def create_test_tickets() -> None:
    """Create 5 random tickets for each team."""
    async with async_session_maker() as session:
        # Get or create citizen user as reporter
        result = await session.execute(
            select(User).where(User.email == "citizen@example.com")
        )
        citizen = result.scalar_one_or_none()
        
        if not citizen:
            print("⚠️  Citizen user not found. Creating one...")
            citizen = User(
                name="Test Citizen",
                email="citizen@example.com",
                phone_number="+905551234567",
                password_hash=hash_password("test123!"),
                role=UserRole.CITIZEN,
                is_verified=True,
                is_active=True,
            )
            session.add(citizen)
            await session.commit()
            print("✅ Citizen user created: citizen@example.com")
        
        # Get all test teams
        result = await session.execute(
            select(Team, Category, District)
            .join(TeamCategory, Team.id == TeamCategory.team_id)
            .join(Category, TeamCategory.category_id == Category.id)
            .join(TeamDistrict, Team.id == TeamDistrict.team_id)
            .join(District, TeamDistrict.district_id == District.id)
            .where(Team.name.like("%Traffic Team%") | Team.name.like("%Infrastructure Team%"))
        )
        
        teams_data = {}
        for team, category, district in result.all():
            if team.id not in teams_data:
                teams_data[team.id] = {
                    "team": team,
                    "categories": set(),
                    "districts": set(),
                }
            teams_data[team.id]["categories"].add(category)
            teams_data[team.id]["districts"].add(district)
        
        tickets_created = 0
        statuses = [TicketStatus.NEW, TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED]
        
        for team_id, data in teams_data.items():
            team = data["team"]
            categories = list(data["categories"])
            districts = list(data["districts"])
            
            if not categories or not districts:
                continue
            
            category = categories[0]
            district = districts[0]
            
            # Choose issue templates based on category
            if "traffic" in category.name.lower():
                issue_templates = TRAFFIC_ISSUES
            else:
                issue_templates = INFRASTRUCTURE_ISSUES
            
            # Get locations for this district
            locations = DISTRICT_LOCATIONS.get(district.name, [(41.0082, 28.9784)])
            
            print(f"Creating tickets for {team.name}...")
            
            for i in range(5):
                # Random issue
                issue = random.choice(issue_templates)
                
                # Random location in district
                lat, lon = random.choice(locations)
                # Add small random offset
                lat += random.uniform(-0.005, 0.005)
                lon += random.uniform(-0.005, 0.005)
                
                # Create location
                location = Location(
                    latitude=lat,
                    longitude=lon,
                    address=f"{district.name}, Istanbul",
                    district=district.name,
                    city="Istanbul",
                    coordinates=f"POINT({lon} {lat})",
                )
                session.add(location)
                await session.flush()
                
                # Random status
                status = random.choice(statuses)
                
                # Create ticket
                ticket = Ticket(
                    title=issue,
                    description=f"Lütfen {issue.lower()} sorununa bakın. {district.name} bölgesinde.",
                    category_id=category.id,
                    location_id=location.id,
                    reporter_id=citizen.id,
                    team_id=team.id,
                    status=status,
                )
                session.add(ticket)
                tickets_created += 1
            
            await session.commit()
            print(f"   ✅ Created 5 tickets for {team.name}")
        
        print("\n" + "="*60)
        print(f"✅ Ticket creation complete!")
        print(f"   Total tickets created: {tickets_created}")
        print(f"   Teams: {len(teams_data)}")
        print(f"   Tickets per team: 5")
        print("="*60)


async def main():
    """Main entry point."""
    print("🌱 Starting test data seeding...")
    print(f"   Districts: {', '.join(TEST_DISTRICTS)}")
    print(f"   Categories: {', '.join(TEST_CATEGORIES)}")
    print(f"   Users per team: 2")
    print(f"   Tickets per team: 5")
    print()
    
    await create_test_teams_and_users()
    print("\n")
    await create_test_tickets()


if __name__ == "__main__":
    asyncio.run(main())

