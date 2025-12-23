"""Integration tests for Ticket Follow/Unfollow API endpoints."""

import uuid

from httpx import AsyncClient

from tests.conftest import auth_headers


# ============================================================================
# POST /api/v1/tickets/{id}/follow - Follow ticket
# ============================================================================


class TestFollowTicket:
    """Tests for POST /api/v1/tickets/{id}/follow."""

    async def test_citizen_follows_ticket(
        self, client: AsyncClient, citizen_token: str, ticket
    ):
        """Citizen should be able to follow a ticket."""
        response = await client.post(
            f"/api/v1/tickets/{ticket.id}/follow",
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 201
        data = response.json()
        assert "message" in data

    async def test_follow_ticket_twice_returns_already_following(
        self, client: AsyncClient, citizen_token: str, ticket
    ):
        """Following a ticket twice should indicate already following."""
        # First follow
        await client.post(
            f"/api/v1/tickets/{ticket.id}/follow",
            headers=auth_headers(citizen_token),
        )
        # Second follow
        response = await client.post(
            f"/api/v1/tickets/{ticket.id}/follow",
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 201
        data = response.json()
        assert "Already following" in data["message"]

    async def test_follow_nonexistent_ticket_returns_404(
        self, client: AsyncClient, citizen_token: str
    ):
        """Should return 404 for nonexistent ticket."""
        response = await client.post(
            f"/api/v1/tickets/{uuid.uuid4()}/follow",
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 404

    async def test_unauthenticated_cannot_follow(self, client: AsyncClient, ticket):
        """Unauthenticated requests should be rejected."""
        response = await client.post(f"/api/v1/tickets/{ticket.id}/follow")
        assert response.status_code == 401


# ============================================================================
# DELETE /api/v1/tickets/{id}/follow - Unfollow ticket
# ============================================================================


class TestUnfollowTicket:
    """Tests for DELETE /api/v1/tickets/{id}/follow."""

    async def test_citizen_unfollows_ticket(
        self, client: AsyncClient, citizen_token: str, ticket
    ):
        """Citizen should be able to unfollow a ticket they are following."""
        # First follow
        await client.post(
            f"/api/v1/tickets/{ticket.id}/follow",
            headers=auth_headers(citizen_token),
        )
        # Then unfollow
        response = await client.delete(
            f"/api/v1/tickets/{ticket.id}/follow",
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 204

    async def test_unfollow_ticket_not_following(
        self, client: AsyncClient, citizen_token: str, ticket
    ):
        """Unfollowing a ticket not followed should succeed silently."""
        response = await client.delete(
            f"/api/v1/tickets/{ticket.id}/follow",
            headers=auth_headers(citizen_token),
        )
        # Should succeed even if not following
        assert response.status_code == 204

    async def test_unauthenticated_cannot_unfollow(self, client: AsyncClient, ticket):
        """Unauthenticated requests should be rejected."""
        response = await client.delete(f"/api/v1/tickets/{ticket.id}/follow")
        assert response.status_code == 401
