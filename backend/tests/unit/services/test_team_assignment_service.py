"""Unit tests for TeamAssignmentService."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.district import District
from app.models.team import Team
from app.models.ticket import Ticket, TicketStatus
from app.services.team_assignment_service import TeamAssignmentService


class TestFindMatchingTeam:
    """Tests for TeamAssignmentService.find_matching_team method."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def team(self):
        """Create a test team."""
        return Team(
            id=uuid.uuid4(),
            name="Infrastructure Team",
            description="Handles infrastructure issues",
        )

    @pytest.fixture
    def category_id(self):
        """Create a test category ID."""
        return uuid.uuid4()

    @pytest.fixture
    def district(self):
        """Create a test district."""
        return District(
            id=uuid.uuid4(),
            name="Beyoglu",
            city="Istanbul",
        )

    async def test_find_team_by_category_and_district(
        self, mock_session, team, category_id, district
    ):
        """Should find team that handles both the category AND district (Priority 1)."""
        # First call: district lookup
        district_result = MagicMock()
        district_result.scalar_one_or_none.return_value = district

        # Second call: team lookup by category and district
        team_result = MagicMock()
        team_result.scalar_one_or_none.return_value = team

        mock_session.execute.side_effect = [district_result, team_result]

        result = await TeamAssignmentService.find_matching_team(
            session=mock_session,
            category_id=category_id,
            district="Beyoglu",
            city="Istanbul",
        )

        assert result == team
        assert mock_session.execute.call_count == 2

    async def test_find_team_by_category_in_city(self, mock_session, team, category_id):
        """Should find team by category when district match fails (Priority 2)."""
        # First call: district lookup returns district
        district = District(id=uuid.uuid4(), name="Kadikoy", city="Istanbul")
        district_result = MagicMock()
        district_result.scalar_one_or_none.return_value = district

        # Second call: team by category+district returns None
        no_team_result = MagicMock()
        no_team_result.scalar_one_or_none.return_value = None

        # Third call: team by category in city returns team
        city_team_result = MagicMock()
        city_team_result.scalar_one_or_none.return_value = team

        mock_session.execute.side_effect = [
            district_result,
            no_team_result,
            city_team_result,
        ]

        result = await TeamAssignmentService.find_matching_team(
            session=mock_session,
            category_id=category_id,
            district="Kadikoy",
            city="Istanbul",
        )

        assert result == team
        assert mock_session.execute.call_count == 3

    async def test_find_team_by_category_only(self, mock_session, team, category_id):
        """Should find team by category alone when no district match (Priority 3)."""
        # First call: district lookup returns None (district not found)
        district_result = MagicMock()
        district_result.scalar_one_or_none.return_value = None

        # Second call: team by category in city returns None
        city_team_result = MagicMock()
        city_team_result.scalar_one_or_none.return_value = None

        # Third call: team by category only returns team
        category_team_result = MagicMock()
        category_team_result.scalar_one_or_none.return_value = team

        mock_session.execute.side_effect = [
            district_result,  # District not found
            city_team_result,  # No team in city
            category_team_result,  # Team by category
        ]

        result = await TeamAssignmentService.find_matching_team(
            session=mock_session,
            category_id=category_id,
            district="UnknownDistrict",
            city="Istanbul",
        )

        assert result == team

    async def test_no_matching_team_returns_none(self, mock_session, category_id):
        """Should return None when no team matches (manual assignment required)."""
        # All lookups return None
        no_result = MagicMock()
        no_result.scalar_one_or_none.return_value = None

        mock_session.execute.side_effect = [
            no_result,  # District not found
            no_result,  # No team in city
            no_result,  # No team by category
        ]

        result = await TeamAssignmentService.find_matching_team(
            session=mock_session,
            category_id=category_id,
            district="Nowhere",
            city="Unknown",
        )

        assert result is None

    async def test_find_team_without_district(self, mock_session, team, category_id):
        """Should skip district lookup when district is None."""
        # First call: team by category in city returns None
        city_team_result = MagicMock()
        city_team_result.scalar_one_or_none.return_value = None

        # Second call: team by category only returns team
        category_team_result = MagicMock()
        category_team_result.scalar_one_or_none.return_value = team

        mock_session.execute.side_effect = [city_team_result, category_team_result]

        result = await TeamAssignmentService.find_matching_team(
            session=mock_session,
            category_id=category_id,
            district=None,  # No district provided
            city="Istanbul",
        )

        assert result == team
        # Should not query for district
        assert mock_session.execute.call_count == 2


class TestGetTeamWorkload:
    """Tests for TeamAssignmentService.get_team_workload method."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def team_id(self):
        """Create a test team ID."""
        return uuid.uuid4()

    async def test_workload_counts_active_tickets(self, mock_session, team_id):
        """Should count NEW and IN_PROGRESS tickets."""
        # Create mock tickets
        tickets = [
            Ticket(
                id=uuid.uuid4(),
                status=TicketStatus.NEW,
                team_id=team_id,
            ),
            Ticket(
                id=uuid.uuid4(),
                status=TicketStatus.IN_PROGRESS,
                team_id=team_id,
            ),
            Ticket(
                id=uuid.uuid4(),
                status=TicketStatus.NEW,
                team_id=team_id,
            ),
        ]

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = tickets
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await TeamAssignmentService.get_team_workload(mock_session, team_id)

        assert result == 3

    async def test_workload_returns_zero_for_no_tickets(self, mock_session, team_id):
        """Should return 0 when team has no active tickets."""
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await TeamAssignmentService.get_team_workload(mock_session, team_id)

        assert result == 0

    async def test_workload_excludes_resolved_and_closed(self, mock_session, team_id):
        """Should not count RESOLVED or CLOSED tickets in workload."""
        # The query filters by status IN (NEW, IN_PROGRESS)
        # So the returned tickets should only include active ones
        active_tickets = [
            Ticket(id=uuid.uuid4(), status=TicketStatus.NEW, team_id=team_id),
        ]

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = active_tickets
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await TeamAssignmentService.get_team_workload(mock_session, team_id)

        # Only the NEW ticket should be counted
        assert result == 1
