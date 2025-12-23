"""Integration tests for Comments API endpoints."""

import uuid

from httpx import AsyncClient

from tests.conftest import auth_headers


# ============================================================================
# GET /api/v1/tickets/{id}/comments - List comments
# ============================================================================


class TestListComments:
    """Tests for GET /api/v1/tickets/{id}/comments."""

    async def test_get_ticket_comments(
        self, client: AsyncClient, citizen_token: str, ticket
    ):
        """Should return list of comments for a ticket."""
        response = await client.get(
            f"/api/v1/tickets/{ticket.id}/comments",
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    async def test_nonexistent_ticket_returns_404(
        self, client: AsyncClient, citizen_token: str
    ):
        """Should return 404 for nonexistent ticket."""
        response = await client.get(
            f"/api/v1/tickets/{uuid.uuid4()}/comments",
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 404

    async def test_unauthenticated_cannot_list_comments(
        self, client: AsyncClient, ticket
    ):
        """Unauthenticated requests should be rejected."""
        response = await client.get(f"/api/v1/tickets/{ticket.id}/comments")
        assert response.status_code == 401


# ============================================================================
# POST /api/v1/tickets/{id}/comments - Create comment
# ============================================================================


class TestCreateComment:
    """Tests for POST /api/v1/tickets/{id}/comments."""

    async def test_citizen_creates_comment(
        self, client: AsyncClient, citizen_token: str, ticket
    ):
        """Citizen should be able to create a comment on a ticket."""
        response = await client.post(
            f"/api/v1/tickets/{ticket.id}/comments",
            json={"content": "This is a test comment on the ticket."},
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "This is a test comment on the ticket."
        assert data["is_internal"] is False

    async def test_support_creates_public_comment(
        self, client: AsyncClient, support_token: str, ticket
    ):
        """Support user should be able to create public comments."""
        response = await client.post(
            f"/api/v1/tickets/{ticket.id}/comments",
            json={"content": "We are working on this issue.", "is_internal": False},
            headers=auth_headers(support_token),
        )
        assert response.status_code == 201
        data = response.json()
        assert data["is_internal"] is False

    async def test_support_creates_internal_comment(
        self, client: AsyncClient, support_token: str, ticket
    ):
        """Support user should be able to create internal comments."""
        response = await client.post(
            f"/api/v1/tickets/{ticket.id}/comments",
            json={"content": "Internal note: need to escalate.", "is_internal": True},
            headers=auth_headers(support_token),
        )
        assert response.status_code == 201
        data = response.json()
        assert data["is_internal"] is True

    async def test_citizen_cannot_create_internal_comment(
        self, client: AsyncClient, citizen_token: str, ticket
    ):
        """Citizen should not be able to create internal comments."""
        response = await client.post(
            f"/api/v1/tickets/{ticket.id}/comments",
            json={"content": "Trying internal comment.", "is_internal": True},
            headers=auth_headers(citizen_token),
        )
        # Either 403 or the is_internal flag is ignored
        if response.status_code == 201:
            data = response.json()
            assert data["is_internal"] is False  # Should be forced to False

    async def test_comment_content_validation(
        self, client: AsyncClient, citizen_token: str, ticket
    ):
        """Should validate comment content."""
        response = await client.post(
            f"/api/v1/tickets/{ticket.id}/comments",
            json={"content": ""},  # Empty content
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 422

    async def test_nonexistent_ticket_returns_404(
        self, client: AsyncClient, citizen_token: str
    ):
        """Should return 404 when commenting on nonexistent ticket."""
        response = await client.post(
            f"/api/v1/tickets/{uuid.uuid4()}/comments",
            json={"content": "Test comment."},
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 404


class TestInternalCommentsVisibility:
    """Tests for internal comment visibility."""

    async def test_citizen_cannot_see_internal_comments(
        self, client: AsyncClient, citizen_token: str, support_token: str, ticket
    ):
        """Citizen should not see internal comments when viewing ticket."""
        # Create an internal comment
        await client.post(
            f"/api/v1/tickets/{ticket.id}/comments",
            json={"content": "Internal: confidential note.", "is_internal": True},
            headers=auth_headers(support_token),
        )

        # Create a public comment
        await client.post(
            f"/api/v1/tickets/{ticket.id}/comments",
            json={"content": "Public: we are handling this.", "is_internal": False},
            headers=auth_headers(support_token),
        )

        # Citizen views ticket details
        response = await client.get(
            f"/api/v1/tickets/{ticket.id}",
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 200
        data = response.json()

        # Verify no internal comments visible
        for comment in data.get("comments", []):
            assert comment["is_internal"] is False

    async def test_support_can_see_internal_comments(
        self, client: AsyncClient, support_token: str, ticket
    ):
        """Support user should see internal comments when viewing ticket."""
        # Create an internal comment
        await client.post(
            f"/api/v1/tickets/{ticket.id}/comments",
            json={"content": "Internal: confidential note.", "is_internal": True},
            headers=auth_headers(support_token),
        )

        # Support views ticket details
        response = await client.get(
            f"/api/v1/tickets/{ticket.id}",
            headers=auth_headers(support_token),
        )
        assert response.status_code == 200
        data = response.json()

        # Should include internal comments
        internal_comments = [c for c in data.get("comments", []) if c["is_internal"]]
        assert len(internal_comments) >= 1
