"""Database seed script for default categories and initial data.

Run with: uv run python -m app.scripts.seed
"""

import asyncio
import logging

from sqlalchemy import select

from app.core.security import hash_password
from app.database import async_session_maker, create_tables
from app.models.category import Category
from app.models.user import User, UserRole

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default categories for the SoSoft platform
DEFAULT_CATEGORIES = [
    {
        "name": "Infrastructure",
        "description": "Road damage, sidewalk issues, building problems",
    },
    {
        "name": "Traffic",
        "description": "Traffic signals, road signs, pedestrian crossings",
    },
    {
        "name": "Lighting",
        "description": "Street lights, park lighting, public area illumination",
    },
    {
        "name": "Waste Management",
        "description": "Garbage collection, recycling, illegal dumping",
    },
    {
        "name": "Parks",
        "description": "Park maintenance, playgrounds, green spaces",
    },
    {
        "name": "Other",
        "description": "General neighborhood issues not in other categories",
    },
]

# Default users for the platform (manager and support)
DEFAULT_USERS = [
    {
        "name": "Manager User",
        "email": "manager@sosoft.com",
        "phone_number": "+905001234567",
        "password": "manager123!",
        "role": UserRole.MANAGER,
        "is_verified": True,
    },
    {
        "name": "Support User",
        "email": "support@sosoft.com",
        "phone_number": "+905001234568",
        "password": "support123!",
        "role": UserRole.SUPPORT,
        "is_verified": True,
    },
]


async def seed_categories() -> None:
    """Seed the database with default categories."""
    async with async_session_maker() as session:
        # Check existing categories
        result = await session.execute(select(Category))
        existing = {c.name for c in result.scalars().all()}

        created_count = 0
        for category_data in DEFAULT_CATEGORIES:
            if category_data["name"] not in existing:
                category = Category(
                    name=category_data["name"],
                    description=category_data["description"],
                )
                session.add(category)
                created_count += 1
                logger.info(f"Created category: {category_data['name']}")

        if created_count > 0:
            await session.commit()
            logger.info(f"Successfully created {created_count} categories")
        else:
            logger.info("All default categories already exist")


async def seed_users() -> None:
    """Seed the database with default manager and support users."""
    async with async_session_maker() as session:
        # Check existing users by email
        result = await session.execute(select(User))
        existing_emails = {u.email for u in result.scalars().all()}

        created_count = 0
        for user_data in DEFAULT_USERS:
            if user_data["email"] not in existing_emails:
                user = User(
                    name=user_data["name"],
                    email=user_data["email"],
                    phone_number=user_data["phone_number"],
                    password_hash=hash_password(user_data["password"]),
                    role=user_data["role"],
                    is_verified=user_data["is_verified"],
                )
                session.add(user)
                created_count += 1
                logger.info(
                    f"Created user: {user_data['name']} ({user_data['role'].value})"
                )

        if created_count > 0:
            await session.commit()
            logger.info(f"Successfully created {created_count} users")
        else:
            logger.info("All default users already exist")


async def main() -> None:
    """Main seed function."""
    logger.info("Starting database seed...")

    # Ensure tables exist
    logger.info("Creating tables if not exist...")
    await create_tables()

    # Seed categories
    await seed_categories()

    # Seed users
    await seed_users()

    logger.info("Database seed completed!")


if __name__ == "__main__":
    asyncio.run(main())
