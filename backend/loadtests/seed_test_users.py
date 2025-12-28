"""
Seed script to create test users for load testing.

Run this script before running load tests:
    python -m loadtests.seed_test_users

This creates:
- 1 citizen user (loadtest_citizen@example.com)
- 1 support user (loadtest_support@example.com)
- 1 manager user (loadtest_manager@example.com)
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.config import settings
from app.models.user import User, UserRole
from app.core.security import get_password_hash


# Test user definitions
TEST_USERS = [
    {
        "email": "loadtest_citizen@example.com",
        "password": "LoadTest123!",
        "phone_number": "+905551234567",
        "full_name": "Load Test Citizen",
        "role": UserRole.CITIZEN,
        "is_verified": True,
    },
    {
        "email": "loadtest_support@example.com",
        "password": "LoadTest123!",
        "phone_number": "+905551234568",
        "full_name": "Load Test Support",
        "role": UserRole.SUPPORT,
        "is_verified": True,
    },
    {
        "email": "loadtest_manager@example.com",
        "password": "LoadTest123!",
        "phone_number": "+905551234569",
        "full_name": "Load Test Manager",
        "role": UserRole.MANAGER,
        "is_verified": True,
    },
]


async def create_test_users():
    """Create test users in the database."""
    engine = create_async_engine(settings.database_url, echo=True)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        for user_data in TEST_USERS:
            # Check if user exists
            stmt = select(User).where(User.email == user_data["email"])
            result = await session.execute(stmt)
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print(f"User {user_data['email']} already exists, skipping...")
                continue
            
            # Create new user
            user = User(
                email=user_data["email"],
                hashed_password=get_password_hash(user_data["password"]),
                phone_number=user_data["phone_number"],
                full_name=user_data["full_name"],
                role=user_data["role"],
                is_verified=user_data["is_verified"],
            )
            session.add(user)
            print(f"Created user: {user_data['email']} ({user_data['role'].value})")
        
        await session.commit()
    
    await engine.dispose()
    print("\nTest users seeding completed!")


if __name__ == "__main__":
    asyncio.run(create_test_users())
