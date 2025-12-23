"""Integration tests for Analytics API endpoints."""

import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Category, Team, Ticket, User, UserRole, Feedback
from app.models.ticket import Location, TicketStatus
from tests.conftest import auth_headers


class TestDashboardAnalytics:
    """Tests for Analytics Dashboard API."""

    async def test_manager_can_access_analytics(
        self, client: AsyncClient, manager_token: str
    ):
        """Manager should be able to access analytics dashboard."""
        response = await client.get(
            "/api/v1/analytics/dashboard",
            headers=auth_headers(manager_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_tickets" in data
        assert "open_tickets" in data
        assert "resolved_tickets" in data
        assert "closed_tickets" in data
        assert "escalated_tickets" in data
        assert "resolution_rate" in data

    async def test_support_can_access_analytics(
        self, client: AsyncClient, support_token: str
    ):
        """Support user should also be able to access analytics."""
        response = await client.get(
            "/api/v1/analytics/dashboard",
            headers=auth_headers(support_token),
        )
        assert response.status_code == 200

    async def test_citizen_cannot_access_analytics(
        self, client: AsyncClient, citizen_token: str
    ):
        """Citizen user should not be able to access analytics."""
        response = await client.get(
            "/api/v1/analytics/dashboard",
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 403

    async def test_date_range_filtering(self, client: AsyncClient, manager_token: str):
        """Should support date range filtering via days param."""
        response = await client.get(
            "/api/v1/analytics/dashboard?days=30",
            headers=auth_headers(manager_token),
        )
        assert response.status_code == 200


class TestHeatmapAnalytics:
    """Tests for Heatmap Analytics API."""

    async def test_heatmap_data(self, client: AsyncClient, manager_token: str):
        """Manager should be able to access heatmap data."""
        response = await client.get(
            "/api/v1/analytics/heatmap",
            headers=auth_headers(manager_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert "points" in data
        assert "total_tickets" in data
        assert "max_count" in data

    async def test_heatmap_with_category_filter(
        self, client: AsyncClient, manager_token: str, category: Category
    ):
        """Heatmap should support category filtering."""
        response = await client.get(
            f"/api/v1/analytics/heatmap?category_id={category.id}",
            headers=auth_headers(manager_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert "points" in data

    async def test_heatmap_with_status_filter(
        self, client: AsyncClient, manager_token: str
    ):
        """Heatmap should support status filtering."""
        response = await client.get(
            "/api/v1/analytics/heatmap?status=NEW",
            headers=auth_headers(manager_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert "points" in data

    async def test_heatmap_with_tickets(
        self, client: AsyncClient, manager_token: str, ticket: Ticket
    ):
        """Heatmap should include ticket location data."""
        response = await client.get(
            "/api/v1/analytics/heatmap",
            headers=auth_headers(manager_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_tickets"] >= 1
        if data["points"]:
            point = data["points"][0]
            assert "latitude" in point
            assert "longitude" in point
            assert "count" in point
            assert "intensity" in point

    async def test_citizen_cannot_access_heatmap(
        self, client: AsyncClient, citizen_token: str
    ):
        """Citizen should not be able to access heatmap."""
        response = await client.get(
            "/api/v1/analytics/heatmap",
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 403


class TestTeamPerformanceAnalytics:
    """Tests for Team Performance Analytics API."""

    async def test_manager_can_access_team_performance(
        self, client: AsyncClient, manager_token: str
    ):
        """Manager should be able to access team performance."""
        response = await client.get(
            "/api/v1/analytics/teams",
            headers=auth_headers(manager_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert "teams" in data

    async def test_team_performance_with_team(
        self, client: AsyncClient, manager_token: str, team: Team
    ):
        """Team performance should include team data."""
        response = await client.get(
            "/api/v1/analytics/teams",
            headers=auth_headers(manager_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["teams"]) >= 1
        team_data = data["teams"][0]
        assert "team_id" in team_data
        assert "team_name" in team_data
        assert "total_assigned" in team_data
        assert "total_resolved" in team_data
        assert "resolution_rate" in team_data
        assert "member_count" in team_data

    async def test_team_performance_with_assigned_tickets(
        self,
        client: AsyncClient,
        manager_token: str,
        ticket: Ticket,
        team: Team,
        support_user_with_team: User,  # Ensure team has a member
    ):
        """Team performance should reflect assigned tickets."""
        response = await client.get(
            "/api/v1/analytics/teams",
            headers=auth_headers(manager_token),
        )
        assert response.status_code == 200
        data = response.json()
        # Find our team in the response
        team_data = next(
            (t for t in data["teams"] if str(t["team_id"]) == str(team.id)), None
        )
        assert team_data is not None
        assert team_data["total_assigned"] >= 1
        assert team_data["member_count"] >= 1

    async def test_support_cannot_access_team_performance(
        self, client: AsyncClient, support_token: str
    ):
        """Support user should not be able to access team performance (manager only)."""
        response = await client.get(
            "/api/v1/analytics/teams",
            headers=auth_headers(support_token),
        )
        assert response.status_code == 403

    async def test_citizen_cannot_access_team_performance(
        self, client: AsyncClient, citizen_token: str
    ):
        """Citizen should not be able to access team performance."""
        response = await client.get(
            "/api/v1/analytics/teams",
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 403


class TestTeamMemberPerformanceAnalytics:
    """Tests for Team Member Performance Analytics API."""

    async def test_manager_can_access_member_performance(
        self,
        client: AsyncClient,
        manager_token: str,
        team: Team,
        support_user_with_team: User,
    ):
        """Manager should be able to access team member performance."""
        response = await client.get(
            f"/api/v1/analytics/teams/{team.id}/members",
            headers=auth_headers(manager_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert "members" in data
        assert "team_id" in data
        assert "team_name" in data
        assert len(data["members"]) >= 1

    async def test_member_performance_includes_metrics(
        self,
        client: AsyncClient,
        manager_token: str,
        team: Team,
        support_user_with_team: User,
    ):
        """Member performance should include all metrics."""
        response = await client.get(
            f"/api/v1/analytics/teams/{team.id}/members",
            headers=auth_headers(manager_token),
        )
        assert response.status_code == 200
        data = response.json()
        if data["members"]:
            member = data["members"][0]
            assert "user_id" in member
            assert "user_name" in member
            assert "total_assigned" in member
            assert "total_resolved" in member
            assert "resolution_rate" in member

    async def test_member_performance_nonexistent_team(
        self, client: AsyncClient, manager_token: str
    ):
        """Should return 404 for nonexistent team."""
        fake_id = uuid.uuid4()
        response = await client.get(
            f"/api/v1/analytics/teams/{fake_id}/members",
            headers=auth_headers(manager_token),
        )
        assert response.status_code == 404

    async def test_support_cannot_access_member_performance(
        self, client: AsyncClient, support_token: str, team: Team
    ):
        """Support should not be able to access member performance."""
        response = await client.get(
            f"/api/v1/analytics/teams/{team.id}/members",
            headers=auth_headers(support_token),
        )
        assert response.status_code == 403


class TestCategoryAnalytics:
    """Tests for Category Statistics API."""

    async def test_manager_can_access_category_stats(
        self, client: AsyncClient, manager_token: str
    ):
        """Manager should be able to access category statistics."""
        response = await client.get(
            "/api/v1/analytics/categories",
            headers=auth_headers(manager_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    async def test_category_stats_with_category(
        self, client: AsyncClient, manager_token: str, category: Category
    ):
        """Category stats should include category data."""
        response = await client.get(
            "/api/v1/analytics/categories",
            headers=auth_headers(manager_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        cat_data = data["items"][0]
        assert "category_id" in cat_data
        assert "category_name" in cat_data
        assert "total_tickets" in cat_data
        assert "open_tickets" in cat_data
        assert "resolved_tickets" in cat_data

    async def test_category_stats_with_days_param(
        self, client: AsyncClient, manager_token: str
    ):
        """Category stats should support days parameter."""
        response = await client.get(
            "/api/v1/analytics/categories?days=7",
            headers=auth_headers(manager_token),
        )
        assert response.status_code == 200

    async def test_support_cannot_access_category_stats(
        self, client: AsyncClient, support_token: str
    ):
        """Support should not be able to access category stats."""
        response = await client.get(
            "/api/v1/analytics/categories",
            headers=auth_headers(support_token),
        )
        assert response.status_code == 403

    async def test_citizen_cannot_access_category_stats(
        self, client: AsyncClient, citizen_token: str
    ):
        """Citizen should not be able to access category stats."""
        response = await client.get(
            "/api/v1/analytics/categories",
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 403


class TestNeighborhoodAnalytics:
    """Tests for Neighborhood Statistics API."""

    async def test_manager_can_access_neighborhood_stats(
        self, client: AsyncClient, manager_token: str
    ):
        """Manager should be able to access neighborhood statistics."""
        response = await client.get(
            "/api/v1/analytics/neighborhoods",
            headers=auth_headers(manager_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    async def test_neighborhood_stats_with_ticket(
        self, client: AsyncClient, manager_token: str, ticket: Ticket
    ):
        """Neighborhood stats should include ticket data."""
        response = await client.get(
            "/api/v1/analytics/neighborhoods",
            headers=auth_headers(manager_token),
        )
        assert response.status_code == 200
        data = response.json()
        # Our test ticket has district "Beyoglu"
        if data["items"]:
            item = data["items"][0]
            assert "district" in item
            assert "total_tickets" in item
            assert "category_breakdown" in item

    async def test_neighborhood_stats_limit_param(
        self, client: AsyncClient, manager_token: str
    ):
        """Neighborhood stats should respect limit parameter."""
        response = await client.get(
            "/api/v1/analytics/neighborhoods?limit=3",
            headers=auth_headers(manager_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 3

    async def test_support_cannot_access_neighborhood_stats(
        self, client: AsyncClient, support_token: str
    ):
        """Support should not be able to access neighborhood stats."""
        response = await client.get(
            "/api/v1/analytics/neighborhoods",
            headers=auth_headers(support_token),
        )
        assert response.status_code == 403


class TestFeedbackTrendsAnalytics:
    """Tests for Feedback Trends API."""

    async def test_manager_can_access_feedback_trends(
        self, client: AsyncClient, manager_token: str
    ):
        """Manager should be able to access feedback trends."""
        response = await client.get(
            "/api/v1/analytics/feedback-trends",
            headers=auth_headers(manager_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    async def test_feedback_trends_with_feedback(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        manager_token: str,
        ticket: Ticket,
        citizen_user: User,
    ):
        """Feedback trends should include feedback data."""
        # Create feedback for the ticket
        feedback = Feedback(
            id=uuid.uuid4(),
            ticket_id=ticket.id,
            user_id=citizen_user.id,
            rating=4,
            comment="Good service",
        )
        db_session.add(feedback)
        await db_session.commit()

        response = await client.get(
            "/api/v1/analytics/feedback-trends",
            headers=auth_headers(manager_token),
        )
        assert response.status_code == 200
        data = response.json()
        if data["items"]:
            item = data["items"][0]
            assert "category_id" in item
            assert "category_name" in item
            assert "total_feedbacks" in item
            assert "average_rating" in item
            assert "rating_distribution" in item

    async def test_feedback_trends_with_days_param(
        self, client: AsyncClient, manager_token: str
    ):
        """Feedback trends should support days parameter."""
        response = await client.get(
            "/api/v1/analytics/feedback-trends?days=60",
            headers=auth_headers(manager_token),
        )
        assert response.status_code == 200

    async def test_support_cannot_access_feedback_trends(
        self, client: AsyncClient, support_token: str
    ):
        """Support should not be able to access feedback trends."""
        response = await client.get(
            "/api/v1/analytics/feedback-trends",
            headers=auth_headers(support_token),
        )
        assert response.status_code == 403

    async def test_citizen_cannot_access_feedback_trends(
        self, client: AsyncClient, citizen_token: str
    ):
        """Citizen should not be able to access feedback trends."""
        response = await client.get(
            "/api/v1/analytics/feedback-trends",
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 403
