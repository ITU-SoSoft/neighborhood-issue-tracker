"""Unit tests for analytics API endpoints."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.api.v1.analytics import (
    get_dashboard_kpis,
    get_ticket_heatmap,
    get_team_performance,
    get_team_member_performance,
    get_category_statistics,
    get_neighborhood_statistics,
    get_feedback_trends,
)
from app.core.exceptions import NotFoundException
from app.models.user import User, UserRole
from app.models.category import Category
from app.models.team import Team
from app.models.ticket import TicketStatus


class TestGetDashboardKPIs:
    """Tests for get_dashboard_kpis endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def support_user(self):
        """Create a support user."""
        return User(
            id=uuid.uuid4(),
            phone_number="+905551234567",
            name="Support",
            role=UserRole.SUPPORT,
        )

    async def test_dashboard_kpis_with_data(self, mock_db, support_user):
        """Should return dashboard KPIs with ticket data."""
        # Mock total tickets count
        mock_total = MagicMock()
        mock_total.scalar.return_value = 100

        # Mock status counts
        mock_status = MagicMock()
        mock_status.all.return_value = [
            (TicketStatus.NEW, 20),
            (TicketStatus.IN_PROGRESS, 30),
            (TicketStatus.RESOLVED, 40),
            (TicketStatus.CLOSED, 10),
        ]

        # Mock average rating
        mock_rating = MagicMock()
        mock_rating.scalar.return_value = 4.5

        # Mock average resolution time
        mock_resolution = MagicMock()
        mock_resolution.scalar.return_value = 24.5

        mock_db.execute.side_effect = [
            mock_total,
            mock_status,
            mock_rating,
            mock_resolution,
        ]

        result = await get_dashboard_kpis(mock_db, support_user, days=30)

        assert result.total_tickets == 100
        assert result.open_tickets == 50  # 20 + 30
        assert result.resolved_tickets == 40
        assert result.closed_tickets == 10
        assert result.resolution_rate == 50.0  # (40+10)/100 * 100

    async def test_dashboard_kpis_empty_data(self, mock_db, support_user):
        """Should return zeros when no tickets exist."""
        mock_total = MagicMock()
        mock_total.scalar.return_value = 0

        mock_status = MagicMock()
        mock_status.all.return_value = []

        mock_rating = MagicMock()
        mock_rating.scalar.return_value = None

        mock_resolution = MagicMock()
        mock_resolution.scalar.return_value = None

        mock_db.execute.side_effect = [
            mock_total,
            mock_status,
            mock_rating,
            mock_resolution,
        ]

        result = await get_dashboard_kpis(mock_db, support_user, days=30)

        assert result.total_tickets == 0
        assert result.resolution_rate == 0.0
        assert result.average_rating is None


class TestGetTicketHeatmap:
    """Tests for get_ticket_heatmap endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def support_user(self):
        """Create a support user."""
        return User(
            id=uuid.uuid4(),
            phone_number="+905551234567",
            name="Support",
            role=UserRole.SUPPORT,
        )

    async def test_heatmap_with_data(self, mock_db, support_user):
        """Should return heatmap points with coordinates."""
        # Mock location/ticket data
        mock_result = MagicMock()
        mock_result.all.return_value = [
            MagicMock(latitude=41.0082, longitude=28.9784, count=10),
            MagicMock(latitude=41.0100, longitude=28.9800, count=5),
        ]
        mock_db.execute.return_value = mock_result

        result = await get_ticket_heatmap(
            mock_db, support_user, days=30, category_id=None, status=None
        )

        assert len(result.points) == 2
        assert result.total_tickets == 15
        assert result.max_count == 10
        assert result.points[0].intensity == 1.0  # 10/10

    async def test_heatmap_empty(self, mock_db, support_user):
        """Should return empty heatmap when no tickets."""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await get_ticket_heatmap(
            mock_db, support_user, days=30, category_id=None, status=None
        )

        assert len(result.points) == 0
        assert result.total_tickets == 0
        assert result.max_count == 0

    async def test_heatmap_with_category_filter(self, mock_db, support_user):
        """Should filter heatmap by category."""
        category_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.all.return_value = [
            MagicMock(latitude=41.0082, longitude=28.9784, count=3),
        ]
        mock_db.execute.return_value = mock_result

        result = await get_ticket_heatmap(
            mock_db, support_user, days=30, category_id=category_id, status=None
        )

        assert len(result.points) == 1
        assert result.total_tickets == 3


class TestGetTeamPerformance:
    """Tests for get_team_performance endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def manager_user(self):
        """Create a manager user."""
        return User(
            id=uuid.uuid4(),
            phone_number="+905551234567",
            name="Manager",
            role=UserRole.MANAGER,
        )

    async def test_team_performance_with_teams(self, mock_db, manager_user):
        """Should return performance metrics for all teams."""
        team = Team(id=uuid.uuid4(), name="Infrastructure Team")

        # Mock teams query
        mock_teams = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [team]
        mock_teams.scalars.return_value = mock_scalars

        # Mock member IDs query
        mock_members = MagicMock()
        mock_members.all.return_value = [(uuid.uuid4(),)]

        # Mock total assigned
        mock_assigned = MagicMock()
        mock_assigned.scalar.return_value = 50

        # Mock total resolved
        mock_resolved = MagicMock()
        mock_resolved.scalar.return_value = 40

        # Mock avg resolution time
        mock_avg_time = MagicMock()
        mock_avg_time.scalar.return_value = 12.5

        # Mock avg rating
        mock_avg_rating = MagicMock()
        mock_avg_rating.scalar.return_value = 4.2

        mock_db.execute.side_effect = [
            mock_teams,
            mock_members,
            mock_assigned,
            mock_resolved,
            mock_avg_time,
            mock_avg_rating,
        ]

        result = await get_team_performance(mock_db, manager_user, days=30)

        assert len(result.teams) == 1
        assert result.teams[0].team_name == "Infrastructure Team"
        assert result.teams[0].total_assigned == 50
        assert result.teams[0].total_resolved == 40
        assert result.teams[0].resolution_rate == 80.0

    async def test_team_performance_empty_team(self, mock_db, manager_user):
        """Should handle teams with no members."""
        team = Team(id=uuid.uuid4(), name="Empty Team")

        mock_teams = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [team]
        mock_teams.scalars.return_value = mock_scalars

        # Empty members
        mock_members = MagicMock()
        mock_members.all.return_value = []

        mock_db.execute.side_effect = [mock_teams, mock_members]

        result = await get_team_performance(mock_db, manager_user, days=30)

        assert len(result.teams) == 1
        assert result.teams[0].member_count == 0
        assert result.teams[0].total_assigned == 0


class TestGetTeamMemberPerformance:
    """Tests for get_team_member_performance endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def manager_user(self):
        """Create a manager user."""
        return User(
            id=uuid.uuid4(),
            phone_number="+905551234567",
            name="Manager",
            role=UserRole.MANAGER,
        )

    async def test_member_performance_success(self, mock_db, manager_user):
        """Should return performance metrics for team members."""
        team_id = uuid.uuid4()
        team = Team(id=team_id, name="Test Team")
        member = User(
            id=uuid.uuid4(),
            phone_number="+905551111111",
            name="Support Member",
            role=UserRole.SUPPORT,
            team_id=team_id,
        )

        # Mock team lookup
        mock_team = MagicMock()
        mock_team.scalar_one_or_none.return_value = team

        # Mock members query
        mock_members = MagicMock()
        mock_members_scalars = MagicMock()
        mock_members_scalars.all.return_value = [member]
        mock_members.scalars.return_value = mock_members_scalars

        # Mock stats for member
        mock_assigned = MagicMock()
        mock_assigned.scalar.return_value = 20

        mock_resolved = MagicMock()
        mock_resolved.scalar.return_value = 18

        mock_avg_time = MagicMock()
        mock_avg_time.scalar.return_value = 8.5

        mock_avg_rating = MagicMock()
        mock_avg_rating.scalar.return_value = 4.8

        mock_db.execute.side_effect = [
            mock_team,
            mock_members,
            mock_assigned,
            mock_resolved,
            mock_avg_time,
            mock_avg_rating,
        ]

        result = await get_team_member_performance(
            team_id, mock_db, manager_user, days=30
        )

        assert result.team_id == team_id
        assert result.team_name == "Test Team"
        assert len(result.members) == 1
        assert result.members[0].user_name == "Support Member"

    async def test_member_performance_team_not_found(self, mock_db, manager_user):
        """Should raise NotFoundException for non-existent team."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(NotFoundException):
            await get_team_member_performance(
                uuid.uuid4(), mock_db, manager_user, days=30
            )


class TestGetCategoryStatistics:
    """Tests for get_category_statistics endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def manager_user(self):
        """Create a manager user."""
        return User(
            id=uuid.uuid4(),
            phone_number="+905551234567",
            name="Manager",
            role=UserRole.MANAGER,
        )

    async def test_category_stats_success(self, mock_db, manager_user):
        """Should return statistics for all categories."""
        category = Category(
            id=uuid.uuid4(),
            name="Infrastructure",
            is_active=True,
        )

        # Mock categories query
        mock_categories = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [category]
        mock_categories.scalars.return_value = mock_scalars

        # Mock category stats
        mock_total = MagicMock()
        mock_total.scalar.return_value = 30

        mock_open = MagicMock()
        mock_open.scalar.return_value = 10

        mock_resolved = MagicMock()
        mock_resolved.scalar.return_value = 20

        mock_rating = MagicMock()
        mock_rating.scalar.return_value = 4.3

        mock_db.execute.side_effect = [
            mock_categories,
            mock_total,
            mock_open,
            mock_resolved,
            mock_rating,
        ]

        result = await get_category_statistics(mock_db, manager_user, days=30)

        assert len(result.items) == 1
        assert result.items[0].category_name == "Infrastructure"
        assert result.items[0].total_tickets == 30
        assert result.items[0].open_tickets == 10
        assert result.items[0].resolved_tickets == 20


class TestGetNeighborhoodStatistics:
    """Tests for get_neighborhood_statistics endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def manager_user(self):
        """Create a manager user."""
        return User(
            id=uuid.uuid4(),
            phone_number="+905551234567",
            name="Manager",
            role=UserRole.MANAGER,
        )

    async def test_neighborhood_stats_success(self, mock_db, manager_user):
        """Should return neighborhood statistics."""
        # Mock ticket data with locations
        mock_result = MagicMock()
        mock_result.all.return_value = [
            ("Beyoğlu Address", "Beyoğlu", "Infrastructure", uuid.uuid4()),
            ("Beyoğlu Address 2", "Beyoğlu", "Traffic", uuid.uuid4()),
            ("Kadıköy Address", "Kadıköy", "Lighting", uuid.uuid4()),
        ]
        mock_db.execute.return_value = mock_result

        result = await get_neighborhood_statistics(
            mock_db, manager_user, days=30, limit=5
        )

        assert len(result.items) <= 5
        # Should have Beyoğlu with 2 tickets and Kadıköy with 1

    async def test_neighborhood_stats_empty(self, mock_db, manager_user):
        """Should return empty list when no tickets."""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await get_neighborhood_statistics(
            mock_db, manager_user, days=30, limit=5
        )

        assert len(result.items) == 0


class TestGetFeedbackTrends:
    """Tests for get_feedback_trends endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def manager_user(self):
        """Create a manager user."""
        return User(
            id=uuid.uuid4(),
            phone_number="+905551234567",
            name="Manager",
            role=UserRole.MANAGER,
        )

    async def test_feedback_trends_with_data(self, mock_db, manager_user):
        """Should return feedback trends by category."""

        category = Category(
            id=uuid.uuid4(),
            name="Infrastructure",
            is_active=True,
        )

        # Create mock feedbacks
        feedback1 = MagicMock()
        feedback1.rating = 5
        feedback2 = MagicMock()
        feedback2.rating = 4
        feedback3 = MagicMock()
        feedback3.rating = 5

        # Mock categories query
        mock_categories = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [category]
        mock_categories.scalars.return_value = mock_scalars

        # Mock feedbacks query
        mock_feedbacks = MagicMock()
        mock_feedbacks_scalars = MagicMock()
        mock_feedbacks_scalars.all.return_value = [feedback1, feedback2, feedback3]
        mock_feedbacks.scalars.return_value = mock_feedbacks_scalars

        mock_db.execute.side_effect = [mock_categories, mock_feedbacks]

        result = await get_feedback_trends(mock_db, manager_user, days=30)

        assert len(result.items) == 1
        assert result.items[0].category_name == "Infrastructure"
        assert result.items[0].total_feedbacks == 3
        assert result.items[0].average_rating == 4.67  # (5+4+5)/3

    async def test_feedback_trends_no_feedback(self, mock_db, manager_user):
        """Should skip categories with no feedback."""
        category = Category(
            id=uuid.uuid4(),
            name="Empty Category",
            is_active=True,
        )

        mock_categories = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [category]
        mock_categories.scalars.return_value = mock_scalars

        mock_feedbacks = MagicMock()
        mock_feedbacks_scalars = MagicMock()
        mock_feedbacks_scalars.all.return_value = []
        mock_feedbacks.scalars.return_value = mock_feedbacks_scalars

        mock_db.execute.side_effect = [mock_categories, mock_feedbacks]

        result = await get_feedback_trends(mock_db, manager_user, days=30)

        assert len(result.items) == 0
