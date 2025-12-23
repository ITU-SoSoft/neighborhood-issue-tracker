"""Unit tests for categories API endpoints."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.api.v1.categories import (
    list_categories,
    get_category,
    create_category,
    update_category,
)
from app.core.exceptions import CategoryNotFoundException, ConflictException
from app.models.category import Category
from app.models.user import User, UserRole
from app.schemas.category import CategoryCreate, CategoryUpdate


class TestListCategories:
    """Tests for list_categories endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        return db

    async def test_list_categories_active_only(self, mock_db):
        """Should return only active categories by default."""
        now = datetime.now(timezone.utc)
        categories = [
            Category(
                id=uuid.uuid4(),
                name="Roads",
                description="Road issues",
                is_active=True,
                created_at=now,
                updated_at=now,
            ),
            Category(
                id=uuid.uuid4(),
                name="Parks",
                description="Park issues",
                is_active=True,
                created_at=now,
                updated_at=now,
            ),
        ]

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = categories
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        result = await list_categories(mock_db, active_only=True)

        assert result.total == 2
        assert len(result.items) == 2

    async def test_list_categories_include_inactive(self, mock_db):
        """Should return all categories when active_only=False."""
        now = datetime.now(timezone.utc)
        categories = [
            Category(
                id=uuid.uuid4(),
                name="Roads",
                is_active=True,
                created_at=now,
                updated_at=now,
            ),
            Category(
                id=uuid.uuid4(),
                name="Deprecated",
                is_active=False,
                created_at=now,
                updated_at=now,
            ),
        ]

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = categories
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        result = await list_categories(mock_db, active_only=False)

        assert result.total == 2


class TestGetCategory:
    """Tests for get_category endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        return db

    async def test_get_category_success(self, mock_db):
        """Should return a category by ID."""
        category_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        category = Category(
            id=category_id,
            name="Roads",
            description="Road issues",
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = category
        mock_db.execute.return_value = mock_result

        result = await get_category(category_id, mock_db)

        assert result.id == category_id
        assert result.name == "Roads"

    async def test_get_category_not_found(self, mock_db):
        """Should raise CategoryNotFoundException when not found."""
        category_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(CategoryNotFoundException):
            await get_category(category_id, mock_db)


class TestCreateCategory:
    """Tests for create_category endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        return db

    @pytest.fixture
    def manager_user(self):
        """Create a mock manager user."""
        return User(
            id=uuid.uuid4(),
            phone_number="+905551234567",
            name="Manager",
            role=UserRole.MANAGER,
            is_verified=True,
        )

    async def test_create_category_success(self, mock_db, manager_user):
        """Should create a new category."""
        request = CategoryCreate(name="New Category", description="Description")

        # Mock: no existing category
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        async def mock_refresh(cat):
            cat.id = uuid.uuid4()
            cat.created_at = datetime.now(timezone.utc)
            cat.updated_at = datetime.now(timezone.utc)
            cat.is_active = True

        mock_db.refresh = mock_refresh

        result = await create_category(request, manager_user, mock_db)

        assert result.name == "New Category"
        mock_db.add.assert_called_once()

    async def test_create_category_duplicate_name(self, mock_db, manager_user):
        """Should raise ConflictException for duplicate name."""
        request = CategoryCreate(name="Roads", description="Description")

        # Mock: existing category
        existing = Category(id=uuid.uuid4(), name="Roads")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        mock_db.execute.return_value = mock_result

        with pytest.raises(ConflictException):
            await create_category(request, manager_user, mock_db)


class TestUpdateCategory:
    """Tests for update_category endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        return db

    @pytest.fixture
    def manager_user(self):
        """Create a mock manager user."""
        return User(
            id=uuid.uuid4(),
            phone_number="+905551234567",
            name="Manager",
            role=UserRole.MANAGER,
            is_verified=True,
        )

    async def test_update_category_success(self, mock_db, manager_user):
        """Should update a category."""
        category_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        category = Category(
            id=category_id,
            name="Roads",
            description="Old description",
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = category
        mock_db.execute.return_value = mock_result

        request = CategoryUpdate(description="New description")

        result = await update_category(category_id, request, manager_user, mock_db)

        assert result.description == "New description"

    async def test_update_category_not_found(self, mock_db, manager_user):
        """Should raise CategoryNotFoundException when not found."""
        category_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        request = CategoryUpdate(description="New description")

        with pytest.raises(CategoryNotFoundException):
            await update_category(category_id, request, manager_user, mock_db)

    async def test_update_category_duplicate_name(self, mock_db, manager_user):
        """Should raise ConflictException for duplicate name."""
        category_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        category = Category(
            id=category_id,
            name="Roads",
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        # First call: find category, second call: find duplicate
        mock_result1 = MagicMock()
        mock_result1.scalar_one_or_none.return_value = category
        mock_result2 = MagicMock()
        mock_result2.scalar_one_or_none.return_value = Category(
            id=uuid.uuid4(), name="Parks"
        )

        mock_db.execute.side_effect = [mock_result1, mock_result2]

        request = CategoryUpdate(name="Parks")

        with pytest.raises(ConflictException):
            await update_category(category_id, request, manager_user, mock_db)

    async def test_update_category_deactivate(self, mock_db, manager_user):
        """Should deactivate a category."""
        category_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        category = Category(
            id=category_id,
            name="Roads",
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = category
        mock_db.execute.return_value = mock_result

        request = CategoryUpdate(is_active=False)

        result = await update_category(category_id, request, manager_user, mock_db)

        assert result.is_active is False
