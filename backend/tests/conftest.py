"""Pytest configuration and fixtures for testing."""

import os
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.config import settings
from app.core.security import create_access_token
from app.database import Base, get_async_session
from app.models import Category, OTPCode, Team, User, UserRole
from main import app
import app.database as database_module


# Use PostgreSQL with PostGIS for testing (requires running docker-compose)
# Default to the docker-compose database, but use a separate test database
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/sosoft_test",
)

# Synchronous URL for setup operations
TEST_DATABASE_URL_SYNC = TEST_DATABASE_URL.replace("+asyncpg", "")


def _setup_test_database():
    """Create the test database if it doesn't exist (synchronous helper)."""
    # Connect to default postgres database to create test database
    admin_url = TEST_DATABASE_URL_SYNC.rsplit("/", 1)[0] + "/postgres"
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")

    with admin_engine.connect() as conn:
        # Check if test database exists
        result = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = 'sosoft_test'")
        )
        exists = result.scalar() is not None

        if not exists:
            conn.execute(text("CREATE DATABASE sosoft_test"))

    admin_engine.dispose()

    # Now connect to test database and enable PostGIS
    test_engine = create_engine(TEST_DATABASE_URL_SYNC)
    with test_engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))

    test_engine.dispose()


# Run setup once at module import time
_setup_test_database()


@pytest_asyncio.fixture(scope="function")
async def async_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create async engine for testing."""
    # Use NullPool to avoid connection sharing issues between tests
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )

    # Patch both the global engine and async_session_maker in app.database
    original_engine = database_module.engine
    original_session_maker = database_module.async_session_maker

    # Create new session maker with our test engine
    test_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    database_module.engine = engine
    database_module.async_session_maker = test_session_maker

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    # Restore originals
    database_module.engine = original_engine
    database_module.async_session_maker = original_session_maker

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(async_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    async_session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(
    async_engine: AsyncEngine,
) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with overridden database session."""
    # Create a session maker bound to our test engine
    test_session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async def override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
        async with test_session_maker() as session:
            try:
                yield session
            finally:
                await session.close()

    app.dependency_overrides[get_async_session] = override_get_async_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# ============================================================================
# User fixtures
# ============================================================================


@pytest_asyncio.fixture
async def citizen_user(db_session: AsyncSession) -> User:
    """Create a verified citizen user for testing."""
    user = User(
        id=uuid.uuid4(),
        phone_number="+905551234567",
        name="Test Citizen",
        email="citizen@test.com",
        role=UserRole.CITIZEN,
        is_verified=True,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def support_user(db_session: AsyncSession) -> User:
    """Create a verified support user for testing."""
    user = User(
        id=uuid.uuid4(),
        phone_number="+905559876543",
        name="Test Support",
        email="support@test.com",
        role=UserRole.SUPPORT,
        is_verified=True,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def manager_user(db_session: AsyncSession) -> User:
    """Create a verified manager user for testing."""
    user = User(
        id=uuid.uuid4(),
        phone_number="+905551112233",
        name="Test Manager",
        email="manager@test.com",
        role=UserRole.MANAGER,
        is_verified=True,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def unverified_user(db_session: AsyncSession) -> User:
    """Create an unverified user for testing."""
    user = User(
        id=uuid.uuid4(),
        phone_number="+905554445566",
        name="Unverified User",
        role=UserRole.CITIZEN,
        is_verified=False,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


# ============================================================================
# Token fixtures
# ============================================================================


@pytest.fixture
def citizen_token(citizen_user: User) -> str:
    """Create JWT token for citizen user."""
    return create_access_token(data={"sub": str(citizen_user.id)})


@pytest.fixture
def support_token(support_user: User) -> str:
    """Create JWT token for support user."""
    return create_access_token(data={"sub": str(support_user.id)})


@pytest.fixture
def manager_token(manager_user: User) -> str:
    """Create JWT token for manager user."""
    return create_access_token(data={"sub": str(manager_user.id)})


def auth_headers(token: str) -> dict[str, str]:
    """Create authorization headers with bearer token."""
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# Category fixtures
# ============================================================================


@pytest_asyncio.fixture
async def category(db_session: AsyncSession) -> Category:
    """Create a test category."""
    cat = Category(
        id=uuid.uuid4(),
        name="Infrastructure",
        description="Infrastructure issues",
        is_active=True,
    )
    db_session.add(cat)
    await db_session.commit()
    await db_session.refresh(cat)
    return cat


@pytest_asyncio.fixture
async def categories(db_session: AsyncSession) -> list[Category]:
    """Create multiple test categories."""
    cats = [
        Category(id=uuid.uuid4(), name="Infrastructure", is_active=True),
        Category(id=uuid.uuid4(), name="Traffic", is_active=True),
        Category(id=uuid.uuid4(), name="Lighting", is_active=True),
        Category(id=uuid.uuid4(), name="Waste Management", is_active=True),
        Category(id=uuid.uuid4(), name="Parks", is_active=True),
        Category(id=uuid.uuid4(), name="Other", is_active=True),
    ]
    for cat in cats:
        db_session.add(cat)
    await db_session.commit()
    for cat in cats:
        await db_session.refresh(cat)
    return cats


# ============================================================================
# Team fixtures
# ============================================================================


@pytest_asyncio.fixture
async def team(db_session: AsyncSession) -> Team:
    """Create a test team."""
    t = Team(
        id=uuid.uuid4(),
        name="Infrastructure Team",
        description="Handles infrastructure issues",
    )
    db_session.add(t)
    await db_session.commit()
    await db_session.refresh(t)
    return t


# ============================================================================
# OTP fixtures
# ============================================================================


@pytest_asyncio.fixture
async def valid_otp(db_session: AsyncSession) -> OTPCode:
    """Create a valid OTP code."""
    otp = OTPCode(
        id=uuid.uuid4(),
        phone_number="+905557778899",
        code="123456",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        is_used=False,
    )
    db_session.add(otp)
    await db_session.commit()
    await db_session.refresh(otp)
    return otp


@pytest_asyncio.fixture
async def expired_otp(db_session: AsyncSession) -> OTPCode:
    """Create an expired OTP code."""
    otp = OTPCode(
        id=uuid.uuid4(),
        phone_number="+905557778899",
        code="654321",
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=5),
        is_used=False,
    )
    db_session.add(otp)
    await db_session.commit()
    await db_session.refresh(otp)
    return otp
