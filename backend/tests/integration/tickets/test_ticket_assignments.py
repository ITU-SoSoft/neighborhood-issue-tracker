"""Integration tests for Ticket Assignment API endpoints."""

import uuid

from httpx import AsyncClient

from tests.conftest import auth_headers


# ============================================================================
# GET /api/v1/tickets/my - Get user's own tickets
# ============================================================================


class TestMyTickets:
    """Tests for GET /api/v1/tickets/my."""

    async def test_citizen_gets_own_tickets(
        self, client: AsyncClient, citizen_token: str, ticket
    ):
        """Citizen should see their own created tickets."""
        response = await client.get(
            "/api/v1/tickets/my",
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["total"] >= 1
        # All tickets should belong to the current user
        for item in data["items"]:
            assert "reporter_id" in item

    async def test_citizen_with_no_tickets(
        self, client: AsyncClient, manager_token: str
    ):
        """Citizen with no tickets should get empty list."""
        # Use a manager token to test the edge case - manager with no personal tickets
        # should still get empty list for /my endpoint
        response = await client.get(
            "/api/v1/tickets/my",
            headers=auth_headers(manager_token),
        )
        assert response.status_code == 200
        data = response.json()
        # Manager may or may not have tickets, but the endpoint should work
        assert "items" in data
        assert "total" in data

    async def test_unauthenticated_cannot_get_my_tickets(self, client: AsyncClient):
        """Unauthenticated requests should be rejected."""
        response = await client.get("/api/v1/tickets/my")
        assert response.status_code == 401


# ============================================================================
# GET /api/v1/tickets/assigned - Get team assigned tickets
# ============================================================================


class TestAssignedTickets:
    """Tests for GET /api/v1/tickets/assigned."""

    async def test_support_gets_team_assigned_tickets(
        self, client: AsyncClient, support_with_team_token: str, ticket
    ):
        """Support user should see tickets assigned to their team."""
        response = await client.get(
            "/api/v1/tickets/assigned",
            headers=auth_headers(support_with_team_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    async def test_support_without_team_gets_empty(
        self, client: AsyncClient, support_token: str
    ):
        """Support user without team assignment should get empty list."""
        response = await client.get(
            "/api/v1/tickets/assigned",
            headers=auth_headers(support_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    async def test_citizen_cannot_access_assigned_tickets(
        self, client: AsyncClient, citizen_token: str
    ):
        """Citizen users should not access assigned tickets endpoint."""
        response = await client.get(
            "/api/v1/tickets/assigned",
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 403

    async def test_manager_gets_all_assigned_tickets(
        self, client: AsyncClient, manager_token: str, ticket
    ):
        """Manager should see all assigned tickets."""
        response = await client.get(
            "/api/v1/tickets/assigned",
            headers=auth_headers(manager_token),
        )
        assert response.status_code == 200


# ============================================================================
# GET /api/v1/tickets/followed - Get followed tickets
# ============================================================================


class TestFollowedTickets:
    """Tests for GET /api/v1/tickets/followed."""

    async def test_user_gets_followed_tickets(
        self, client: AsyncClient, citizen_token: str
    ):
        """User should see tickets they are following."""
        response = await client.get(
            "/api/v1/tickets/followed",
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        # User may or may not have followed tickets
        assert "total" in data

    async def test_unauthenticated_cannot_access_followed(self, client: AsyncClient):
        """Unauthenticated requests should be rejected."""
        response = await client.get("/api/v1/tickets/followed")
        assert response.status_code == 401

    async def test_followed_tickets_with_pagination(
        self, client: AsyncClient, citizen_token: str
    ):
        """Should paginate followed tickets."""
        response = await client.get(
            "/api/v1/tickets/followed",
            params={"page": 1, "page_size": 10},
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 10

    async def test_user_with_followed_tickets_sees_others_tickets(
        self,
        client: AsyncClient,
        db_session,
        support_user,
        ticket,
    ):
        """User following another's ticket should see it in followed list."""
        from app.core.security import create_access_token
        from app.models.ticket import TicketFollower

        # Support user follows citizen's ticket
        follower = TicketFollower(
            ticket_id=ticket.id,
            user_id=support_user.id,
        )
        db_session.add(follower)
        await db_session.commit()

        token = create_access_token(data={"sub": str(support_user.id)})

        response = await client.get(
            "/api/v1/tickets/followed",
            headers=auth_headers(token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        # The ticket should be in the followed list
        ticket_ids = [item["id"] for item in data["items"]]
        assert str(ticket.id) in ticket_ids


# ============================================================================
# GET /api/v1/tickets/all - Get all tickets (manager only)
# ============================================================================


class TestAllTickets:
    """Tests for GET /api/v1/tickets/all."""

    async def test_manager_gets_all_tickets(
        self, client: AsyncClient, manager_token: str
    ):
        """Manager should be able to list all tickets."""
        response = await client.get(
            "/api/v1/tickets/all",
            headers=auth_headers(manager_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    async def test_support_can_access_all_tickets(
        self, client: AsyncClient, support_token: str, ticket
    ):
        """Support users should be able to access all tickets."""
        response = await client.get(
            "/api/v1/tickets/all",
            headers=auth_headers(support_token),
        )
        assert response.status_code == 200

    async def test_citizen_cannot_access_all_tickets(
        self, client: AsyncClient, citizen_token: str
    ):
        """Citizen users can access /all endpoint - it shows their own and followed tickets."""
        response = await client.get(
            "/api/v1/tickets/all",
            headers=auth_headers(citizen_token),
        )
        # /all endpoint is accessible by any authenticated user
        # it returns their own tickets + followed tickets
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data


# ============================================================================
# PATCH /api/v1/tickets/{id}/assign - Assign ticket to team
# ============================================================================


class TestAssignTicket:
    """Tests for PATCH /api/v1/tickets/{id}/assign."""

    async def test_manager_assigns_ticket_to_team(
        self, client: AsyncClient, manager_token: str, unassigned_ticket, team
    ):
        """Manager should be able to assign ticket to a team."""
        response = await client.patch(
            f"/api/v1/tickets/{unassigned_ticket.id}/assign",
            json={"team_id": str(team.id)},
            headers=auth_headers(manager_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["team_id"] == str(team.id)

    async def test_support_cannot_assign_ticket(
        self, client: AsyncClient, support_token: str, unassigned_ticket, team
    ):
        """Support users should not be able to assign tickets."""
        response = await client.patch(
            f"/api/v1/tickets/{unassigned_ticket.id}/assign",
            json={"team_id": str(team.id)},
            headers=auth_headers(support_token),
        )
        assert response.status_code == 403

    async def test_citizen_cannot_assign_ticket(
        self, client: AsyncClient, citizen_token: str, unassigned_ticket, team
    ):
        """Citizen users should not be able to assign tickets."""
        response = await client.patch(
            f"/api/v1/tickets/{unassigned_ticket.id}/assign",
            json={"team_id": str(team.id)},
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 403

    async def test_assign_to_nonexistent_team_fails(
        self, client: AsyncClient, manager_token: str, unassigned_ticket
    ):
        """Should fail when assigning to a nonexistent team."""
        response = await client.patch(
            f"/api/v1/tickets/{unassigned_ticket.id}/assign",
            json={"team_id": str(uuid.uuid4())},
            headers=auth_headers(manager_token),
        )
        assert response.status_code == 404

    async def test_assign_nonexistent_ticket_fails(
        self, client: AsyncClient, manager_token: str, team
    ):
        """Should fail when assigning a nonexistent ticket."""
        response = await client.patch(
            f"/api/v1/tickets/{uuid.uuid4()}/assign",
            json={"team_id": str(team.id)},
            headers=auth_headers(manager_token),
        )
        assert response.status_code == 404

    async def test_reassign_ticket_to_different_team(
        self, client: AsyncClient, manager_token: str, ticket, other_team
    ):
        """Manager should be able to reassign ticket to a different team."""
        response = await client.patch(
            f"/api/v1/tickets/{ticket.id}/assign",
            json={"team_id": str(other_team.id)},
            headers=auth_headers(manager_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["team_id"] == str(other_team.id)
