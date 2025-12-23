"""Unit tests for teams API endpoints."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.api.v1.teams import (
    list_teams,
    get_team,
    create_team,
    update_team,
    delete_team,
    add_team_member,
    remove_team_member,
)
from app.core.exceptions import NotFoundException, ConflictException
from app.models.user import User, UserRole
from app.models.team import Team
from app.schemas.team import TeamCreate, TeamUpdate


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


def make_team(**kwargs) -> Team:
    """Create a Team with all required fields."""
    now = datetime.now(timezone.utc)
    defaults = {
        "id": uuid.uuid4(),
        "name": "Test Team",
        "description": None,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(kwargs)
    team = Team(**defaults)
    if "members" not in kwargs:
        team.members = []
    return team


class TestListTeams:
    """Tests for list_teams endpoint."""

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

    async def test_list_teams_success(self, mock_db, manager_user):
        """Should return list of teams with member counts."""
        team1 = make_team(name="Team 1")
        team2 = make_team(name="Team 2")

        # Mock teams query - list_teams returns list of (Team, member_count) tuples
        mock_result = MagicMock()
        mock_result.all.return_value = [(team1, 3), (team2, 5)]
        mock_db.execute.return_value = mock_result

        result = await list_teams(mock_db, manager_user)

        assert len(result) == 2
        assert result[0].name == "Team 1"

    async def test_list_teams_empty(self, mock_db, manager_user):
        """Should return empty list when no teams exist."""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await list_teams(mock_db, manager_user)

        assert len(result) == 0


class TestGetTeam:
    """Tests for get_team endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.get = AsyncMock()
        return db

    @pytest.fixture
    def manager_user(self):
        """Create a manager user."""
        return make_user(
            phone_number="+905551234567",
            name="Manager",
            role=UserRole.MANAGER,
        )

    async def test_get_team_success(self, mock_db, manager_user):
        """Should return team with members."""
        team_id = uuid.uuid4()
        team = make_team(id=team_id, name="Test Team", description="Description")

        # Mock the helper function's execute call
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = team
        mock_db.execute.return_value = mock_result

        result = await get_team(team_id, mock_db, manager_user)

        assert result.id == team_id
        assert result.name == "Test Team"

    async def test_get_team_not_found(self, mock_db, manager_user):
        """Should raise NotFoundException for non-existent team."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(NotFoundException):
            await get_team(uuid.uuid4(), mock_db, manager_user)


class TestCreateTeam:
    """Tests for create_team endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
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

    async def test_create_team_success(self, mock_db, manager_user):
        """Should create a new team."""
        team_data = TeamCreate(name="New Team", description="Team description")

        # Mock: no existing team with same name
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await create_team(team_data, mock_db, manager_user)

        assert result.name == "New Team"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    async def test_create_team_duplicate_name(self, mock_db, manager_user):
        """Should raise ConflictException for duplicate team name."""
        team_data = TeamCreate(name="Existing Team")

        existing_team = make_team(name="Existing Team")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_team
        mock_db.execute.return_value = mock_result

        with pytest.raises(ConflictException):
            await create_team(team_data, mock_db, manager_user)


class TestUpdateTeam:
    """Tests for update_team endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.execute = AsyncMock()
        db.get = AsyncMock()
        return db

    @pytest.fixture
    def manager_user(self):
        """Create a manager user."""
        return make_user(
            phone_number="+905551234567",
            name="Manager",
            role=UserRole.MANAGER,
        )

    async def test_update_team_success(self, mock_db, manager_user):
        """Should update team details."""
        team_id = uuid.uuid4()
        team = make_team(id=team_id, name="Old Name")

        update_data = TeamUpdate(name="New Name")

        # Mock db.get for team lookup, db.execute for duplicate check
        mock_db.get.return_value = team
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await update_team(team_id, update_data, mock_db, manager_user)

        assert result.name == "New Name"
        mock_db.commit.assert_called_once()

    async def test_update_team_not_found(self, mock_db, manager_user):
        """Should raise NotFoundException for non-existent team."""
        update_data = TeamUpdate(name="New Name")

        mock_db.get.return_value = None

        with pytest.raises(NotFoundException):
            await update_team(uuid.uuid4(), update_data, mock_db, manager_user)

    async def test_update_team_duplicate_name(self, mock_db, manager_user):
        """Should raise ConflictException for duplicate name."""
        team_id = uuid.uuid4()
        team = make_team(id=team_id, name="Team A")

        other_team = make_team(name="Team B")
        update_data = TeamUpdate(name="Team B")

        mock_db.get.return_value = team
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = other_team
        mock_db.execute.return_value = mock_result

        with pytest.raises(ConflictException):
            await update_team(team_id, update_data, mock_db, manager_user)


class TestDeleteTeam:
    """Tests for delete_team endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.commit = AsyncMock()
        db.delete = AsyncMock()
        db.execute = AsyncMock()
        db.get = AsyncMock()
        return db

    @pytest.fixture
    def manager_user(self):
        """Create a manager user."""
        return make_user(
            phone_number="+905551234567",
            name="Manager",
            role=UserRole.MANAGER,
        )

    async def test_delete_team_success(self, mock_db, manager_user):
        """Should delete team and nullify members' team_id."""
        team_id = uuid.uuid4()
        team = make_team(id=team_id, name="Team to Delete")

        mock_db.get.return_value = team

        result = await delete_team(team_id, mock_db, manager_user)

        assert result is None  # HTTP 204 returns None
        mock_db.commit.assert_called()

    async def test_delete_team_not_found(self, mock_db, manager_user):
        """Should raise NotFoundException for non-existent team."""
        mock_db.get.return_value = None

        with pytest.raises(NotFoundException):
            await delete_team(uuid.uuid4(), mock_db, manager_user)


class TestAddTeamMember:
    """Tests for add_team_member endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.execute = AsyncMock()
        db.get = AsyncMock()
        return db

    @pytest.fixture
    def manager_user(self):
        """Create a manager user."""
        return make_user(
            phone_number="+905551234567",
            name="Manager",
            role=UserRole.MANAGER,
        )

    async def test_add_member_success(self, mock_db, manager_user):
        """Should add user to team."""
        team_id = uuid.uuid4()
        user_id = uuid.uuid4()

        team = make_team(id=team_id, name="Test Team")
        user = make_user(
            id=user_id, phone_number="+905551111111", team_id=None, deleted_at=None
        )

        # Mock db.get calls: first for team, second for user
        mock_db.get.side_effect = [team, user]

        # Mock execute for _get_team_with_members helper
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = team
        mock_db.execute.return_value = mock_result

        result = await add_team_member(team_id, user_id, mock_db, manager_user)

        assert user.team_id == team_id
        mock_db.commit.assert_called_once()

    async def test_add_member_team_not_found(self, mock_db, manager_user):
        """Should raise NotFoundException for non-existent team."""
        mock_db.get.return_value = None

        with pytest.raises(NotFoundException):
            await add_team_member(uuid.uuid4(), uuid.uuid4(), mock_db, manager_user)

    async def test_add_member_user_not_found(self, mock_db, manager_user):
        """Should raise NotFoundException for non-existent user."""
        team_id = uuid.uuid4()
        team = make_team(id=team_id, name="Test Team")

        # First call returns team, second returns None (user not found)
        mock_db.get.side_effect = [team, None]

        with pytest.raises(NotFoundException):
            await add_team_member(team_id, uuid.uuid4(), mock_db, manager_user)


class TestRemoveTeamMember:
    """Tests for remove_team_member endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.commit = AsyncMock()
        db.execute = AsyncMock()
        db.get = AsyncMock()
        return db

    @pytest.fixture
    def manager_user(self):
        """Create a manager user."""
        return make_user(
            phone_number="+905551234567",
            name="Manager",
            role=UserRole.MANAGER,
        )

    async def test_remove_member_success(self, mock_db, manager_user):
        """Should remove user from team."""
        team_id = uuid.uuid4()
        user_id = uuid.uuid4()

        team = make_team(id=team_id, name="Test Team")
        user = make_user(
            id=user_id, phone_number="+905551111111", team_id=team_id, deleted_at=None
        )

        mock_db.get.side_effect = [team, user]

        result = await remove_team_member(team_id, user_id, mock_db, manager_user)

        assert user.team_id is None
        assert result is None  # HTTP 204 returns None
        mock_db.commit.assert_called_once()

    async def test_remove_member_not_in_team(self, mock_db, manager_user):
        """Should raise NotFoundException when user not in team."""
        team_id = uuid.uuid4()
        user_id = uuid.uuid4()

        team = make_team(id=team_id, name="Test Team")
        user = make_user(
            id=user_id,
            phone_number="+905551111111",
            team_id=uuid.uuid4(),  # Different team
            deleted_at=None,
        )

        mock_db.get.side_effect = [team, user]

        with pytest.raises(NotFoundException):
            await remove_team_member(team_id, user_id, mock_db, manager_user)
