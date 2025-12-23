"""Unit tests for users API endpoints."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.api.v1.users import (
    list_users,
    get_user,
    update_user,
    update_user_role,
    delete_user,
)
from app.core.exceptions import (
    ForbiddenException,
    NotFoundException,
    BadRequestException,
)
from app.models.user import User, UserRole
from app.schemas.user import UserUpdate, UserRoleUpdate


def make_user(**kwargs) -> User:
    """Create a User with all required fields."""
    now = datetime.now(timezone.utc)
    defaults = {
        "id": uuid.uuid4(),
        "phone_number": "+905551234567",
        "name": "Test User",
        "role": UserRole.CITIZEN,
        "is_verified": True,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(kwargs)
    return User(**defaults)


class TestListUsers:
    """Tests for list_users endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def manager_user(self):
        """Create a manager user."""
        return make_user(
            phone_number="+905551234567",
            name="Manager",
            role=UserRole.MANAGER,
        )

    async def test_list_users_success(self, mock_db, manager_user):
        """Should return paginated list of users."""
        users = [
            make_user(
                phone_number="+905551111111",
                name="User 1",
                role=UserRole.CITIZEN,
            ),
            make_user(
                phone_number="+905552222222",
                name="User 2",
                role=UserRole.SUPPORT,
            ),
        ]

        # Mock count query
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 2

        # Mock users query
        mock_users_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = users
        mock_users_result.scalars.return_value = mock_scalars

        mock_db.execute.side_effect = [mock_count_result, mock_users_result]

        result = await list_users(
            current_user=manager_user,
            db=mock_db,
            role=None,
            team_id=None,
            page=1,
            page_size=10,
        )

        assert result.total == 2
        assert len(result.items) == 2

    async def test_list_users_filter_by_role(self, mock_db, manager_user):
        """Should filter users by role."""
        support_user = make_user(
            phone_number="+905551111111",
            name="Support User",
            role=UserRole.SUPPORT,
        )

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        mock_users_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [support_user]
        mock_users_result.scalars.return_value = mock_scalars

        mock_db.execute.side_effect = [mock_count_result, mock_users_result]

        result = await list_users(
            current_user=manager_user,
            db=mock_db,
            role=UserRole.SUPPORT,
            team_id=None,
            page=1,
            page_size=10,
        )

        assert result.total == 1
        assert result.items[0].role == UserRole.SUPPORT


class TestGetUser:
    """Tests for get_user endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        return db

    async def test_get_own_user(self, mock_db):
        """Should return user's own profile."""
        user_id = uuid.uuid4()
        user = make_user(
            id=user_id,
            phone_number="+905551234567",
            name="Test User",
            role=UserRole.CITIZEN,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user
        mock_db.execute.return_value = mock_result

        result = await get_user(user_id, user, mock_db)

        assert result.id == user_id
        assert result.name == "Test User"

    async def test_manager_can_view_any_user(self, mock_db):
        """Manager should be able to view any user."""
        target_user_id = uuid.uuid4()
        target_user = make_user(
            id=target_user_id,
            phone_number="+905551111111",
            name="Target User",
            role=UserRole.CITIZEN,
        )
        manager = make_user(
            phone_number="+905552222222",
            name="Manager",
            role=UserRole.MANAGER,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = target_user
        mock_db.execute.return_value = mock_result

        result = await get_user(target_user_id, manager, mock_db)

        assert result.id == target_user_id

    async def test_citizen_cannot_view_other_user(self, mock_db):
        """Citizen should not be able to view other users."""
        target_user_id = uuid.uuid4()
        target_user = make_user(
            id=target_user_id,
            phone_number="+905551111111",
            name="Target User",
            role=UserRole.CITIZEN,
        )
        citizen = make_user(
            phone_number="+905552222222",
            name="Citizen",
            role=UserRole.CITIZEN,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = target_user
        mock_db.execute.return_value = mock_result

        with pytest.raises(ForbiddenException):
            await get_user(target_user_id, citizen, mock_db)

    async def test_get_nonexistent_user(self, mock_db):
        """Should raise NotFoundException for non-existent user."""
        manager = make_user(
            phone_number="+905551234567",
            name="Manager",
            role=UserRole.MANAGER,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(NotFoundException):
            await get_user(uuid.uuid4(), manager, mock_db)


class TestUpdateUser:
    """Tests for update_user endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        return db

    async def test_update_own_profile(self, mock_db):
        """Should allow user to update their own profile."""
        user_id = uuid.uuid4()
        user = make_user(
            id=user_id,
            phone_number="+905551234567",
            name="Old Name",
            role=UserRole.CITIZEN,
        )

        update_data = UserUpdate(name="New Name")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user
        mock_db.execute.return_value = mock_result

        result = await update_user(user_id, update_data, user, mock_db)

        assert result.name == "New Name"
        mock_db.commit.assert_called_once()

    async def test_cannot_update_other_user(self, mock_db):
        """Should raise ForbiddenException when updating other user."""
        target_user_id = uuid.uuid4()
        target_user = make_user(
            id=target_user_id,
            phone_number="+905551111111",
            name="Target",
            role=UserRole.CITIZEN,
        )
        current_user = make_user(
            phone_number="+905552222222",
            name="Current",
            role=UserRole.CITIZEN,
        )

        update_data = UserUpdate(name="Hacked Name")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = target_user
        mock_db.execute.return_value = mock_result

        with pytest.raises(ForbiddenException):
            await update_user(target_user_id, update_data, current_user, mock_db)

    async def test_update_phone_conflict(self, mock_db):
        """Should raise BadRequestException for duplicate phone."""
        user_id = uuid.uuid4()
        user = make_user(
            id=user_id,
            phone_number="+905551234567",
            name="User",
            role=UserRole.CITIZEN,
        )

        update_data = UserUpdate(phone_number="+905559999999")

        # First call returns user, second call returns another user with same phone
        mock_result1 = MagicMock()
        mock_result1.scalar_one_or_none.return_value = user
        mock_result2 = MagicMock()
        mock_result2.scalar_one_or_none.return_value = make_user(
            phone_number="+905559999999",
        )
        mock_db.execute.side_effect = [mock_result1, mock_result2]

        with pytest.raises(BadRequestException):
            await update_user(user_id, update_data, user, mock_db)


class TestUpdateUserRole:
    """Tests for update_user_role endpoint."""

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
        """Create a manager user."""
        return make_user(
            phone_number="+905551234567",
            name="Manager",
            role=UserRole.MANAGER,
        )

    async def test_promote_to_support(self, mock_db, manager_user):
        """Manager should be able to promote user to support."""
        target_id = uuid.uuid4()
        target_user = make_user(
            id=target_id,
            phone_number="+905551111111",
            name="Citizen",
            role=UserRole.CITIZEN,
        )

        update_data = UserRoleUpdate(role=UserRole.SUPPORT)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = target_user
        mock_db.execute.return_value = mock_result

        result = await update_user_role(target_id, update_data, manager_user, mock_db)

        assert result.role == UserRole.SUPPORT
        mock_db.commit.assert_called_once()

    async def test_assign_team_with_role(self, mock_db, manager_user):
        """Should assign team when promoting to support."""
        target_id = uuid.uuid4()
        team_id = uuid.uuid4()
        target_user = make_user(
            id=target_id,
            phone_number="+905551111111",
            name="Citizen",
            role=UserRole.CITIZEN,
            team_id=None,
        )

        update_data = UserRoleUpdate(role=UserRole.SUPPORT, team_id=team_id)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = target_user
        mock_db.execute.return_value = mock_result

        result = await update_user_role(target_id, update_data, manager_user, mock_db)

        assert result.role == UserRole.SUPPORT
        assert result.team_id == team_id

    async def test_update_nonexistent_user_role(self, mock_db, manager_user):
        """Should raise NotFoundException for non-existent user."""
        update_data = UserRoleUpdate(role=UserRole.SUPPORT)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(NotFoundException):
            await update_user_role(uuid.uuid4(), update_data, manager_user, mock_db)


class TestDeleteUser:
    """Tests for delete_user endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        return db

    @pytest.fixture
    def manager_user(self):
        """Create a manager user."""
        return make_user(
            phone_number="+905551234567",
            name="Manager",
            role=UserRole.MANAGER,
        )

    async def test_soft_delete_user(self, mock_db, manager_user):
        """Manager should be able to soft delete a user."""
        target_id = uuid.uuid4()
        target_user = make_user(
            id=target_id,
            phone_number="+905551111111",
            name="Target",
            role=UserRole.CITIZEN,
            deleted_at=None,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = target_user
        mock_db.execute.return_value = mock_result

        result = await delete_user(target_id, manager_user, mock_db)

        assert result is None  # HTTP 204 returns None
        assert target_user.deleted_at is not None
        mock_db.commit.assert_called_once()

    async def test_delete_nonexistent_user(self, mock_db, manager_user):
        """Should raise NotFoundException for non-existent user."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(NotFoundException):
            await delete_user(uuid.uuid4(), manager_user, mock_db)
