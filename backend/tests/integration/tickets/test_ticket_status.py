"""Integration tests for Ticket Status API endpoints."""

import uuid

from httpx import AsyncClient

from tests.conftest import auth_headers


# ============================================================================
# PATCH /api/v1/tickets/{id}/status - Update ticket status
# ============================================================================


class TestStatusTransitions:
    """Tests for valid and invalid status transitions."""

    # Valid transitions
    async def test_new_to_in_progress(
        self, client: AsyncClient, support_token: str, ticket
    ):
        """NEW -> IN_PROGRESS is a valid transition."""
        response = await client.patch(
            f"/api/v1/tickets/{ticket.id}/status",
            json={"status": "IN_PROGRESS"},
            headers=auth_headers(support_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "IN_PROGRESS"

    async def test_in_progress_to_resolved(
        self, client: AsyncClient, support_token: str, db_session, ticket
    ):
        """IN_PROGRESS -> RESOLVED is a valid transition."""
        from app.models.ticket import TicketStatus

        ticket.status = TicketStatus.IN_PROGRESS
        await db_session.commit()

        response = await client.patch(
            f"/api/v1/tickets/{ticket.id}/status",
            json={"status": "RESOLVED", "comment": "Issue has been fixed"},
            headers=auth_headers(support_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "RESOLVED"

    async def test_resolved_to_closed(
        self, client: AsyncClient, support_token: str, db_session, ticket
    ):
        """RESOLVED -> CLOSED is a valid transition."""
        from app.models.ticket import TicketStatus

        ticket.status = TicketStatus.RESOLVED
        await db_session.commit()

        response = await client.patch(
            f"/api/v1/tickets/{ticket.id}/status",
            json={"status": "CLOSED"},
            headers=auth_headers(support_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "CLOSED"

    async def test_resolved_to_in_progress_reopen(
        self, client: AsyncClient, support_token: str, db_session, ticket
    ):
        """RESOLVED -> IN_PROGRESS (reopen) is a valid transition."""
        from app.models.ticket import TicketStatus

        ticket.status = TicketStatus.RESOLVED
        await db_session.commit()

        response = await client.patch(
            f"/api/v1/tickets/{ticket.id}/status",
            json={
                "status": "IN_PROGRESS",
                "comment": "Reopening - issue not fully fixed",
            },
            headers=auth_headers(support_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "IN_PROGRESS"

    async def test_new_to_escalated(
        self, client: AsyncClient, support_token: str, ticket
    ):
        """NEW -> ESCALATED is a valid transition."""
        response = await client.patch(
            f"/api/v1/tickets/{ticket.id}/status",
            json={"status": "ESCALATED", "comment": "Needs manager review"},
            headers=auth_headers(support_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ESCALATED"

    async def test_in_progress_to_escalated(
        self, client: AsyncClient, support_token: str, db_session, ticket
    ):
        """IN_PROGRESS -> ESCALATED is a valid transition."""
        from app.models.ticket import TicketStatus

        ticket.status = TicketStatus.IN_PROGRESS
        await db_session.commit()

        response = await client.patch(
            f"/api/v1/tickets/{ticket.id}/status",
            json={"status": "ESCALATED"},
            headers=auth_headers(support_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ESCALATED"

    async def test_escalated_to_in_progress(
        self, client: AsyncClient, support_token: str, db_session, ticket
    ):
        """ESCALATED -> IN_PROGRESS is a valid transition (after review)."""
        from app.models.ticket import TicketStatus

        ticket.status = TicketStatus.ESCALATED
        await db_session.commit()

        response = await client.patch(
            f"/api/v1/tickets/{ticket.id}/status",
            json={
                "status": "IN_PROGRESS",
                "comment": "Escalation reviewed, continuing work",
            },
            headers=auth_headers(support_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "IN_PROGRESS"

    # Invalid transitions
    async def test_new_cannot_jump_to_resolved(
        self, client: AsyncClient, support_token: str, ticket
    ):
        """NEW -> RESOLVED is NOT a valid transition."""
        response = await client.patch(
            f"/api/v1/tickets/{ticket.id}/status",
            json={"status": "RESOLVED"},
            headers=auth_headers(support_token),
        )
        assert response.status_code == 400
        assert "transition" in response.json()["detail"].lower()

    async def test_new_cannot_jump_to_closed(
        self, client: AsyncClient, support_token: str, ticket
    ):
        """NEW -> CLOSED is NOT a valid transition."""
        response = await client.patch(
            f"/api/v1/tickets/{ticket.id}/status",
            json={"status": "CLOSED"},
            headers=auth_headers(support_token),
        )
        assert response.status_code == 400

    async def test_closed_cannot_change(
        self, client: AsyncClient, support_token: str, db_session, ticket
    ):
        """CLOSED tickets cannot transition to any other state."""
        from app.models.ticket import TicketStatus

        ticket.status = TicketStatus.CLOSED
        await db_session.commit()

        response = await client.patch(
            f"/api/v1/tickets/{ticket.id}/status",
            json={"status": "IN_PROGRESS"},
            headers=auth_headers(support_token),
        )
        assert response.status_code == 400

    async def test_in_progress_cannot_jump_to_closed(
        self, client: AsyncClient, support_token: str, db_session, ticket
    ):
        """IN_PROGRESS -> CLOSED is NOT a valid transition (must resolve first)."""
        from app.models.ticket import TicketStatus

        ticket.status = TicketStatus.IN_PROGRESS
        await db_session.commit()

        response = await client.patch(
            f"/api/v1/tickets/{ticket.id}/status",
            json={"status": "CLOSED"},
            headers=auth_headers(support_token),
        )
        assert response.status_code == 400


class TestStatusPermissions:
    """Tests for status change permissions."""

    async def test_citizen_cannot_change_status(
        self, client: AsyncClient, citizen_token: str, ticket
    ):
        """Citizen users cannot change ticket status."""
        response = await client.patch(
            f"/api/v1/tickets/{ticket.id}/status",
            json={"status": "IN_PROGRESS"},
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 403

    async def test_support_can_change_status(
        self, client: AsyncClient, support_token: str, ticket
    ):
        """Support users can change ticket status."""
        response = await client.patch(
            f"/api/v1/tickets/{ticket.id}/status",
            json={"status": "IN_PROGRESS"},
            headers=auth_headers(support_token),
        )
        assert response.status_code == 200

    async def test_manager_can_change_status(
        self, client: AsyncClient, manager_token: str, ticket
    ):
        """Manager users can change any ticket status."""
        response = await client.patch(
            f"/api/v1/tickets/{ticket.id}/status",
            json={"status": "IN_PROGRESS"},
            headers=auth_headers(manager_token),
        )
        assert response.status_code == 200

    async def test_unauthenticated_cannot_change_status(
        self, client: AsyncClient, ticket
    ):
        """Unauthenticated requests should be rejected."""
        response = await client.patch(
            f"/api/v1/tickets/{ticket.id}/status",
            json={"status": "IN_PROGRESS"},
        )
        assert response.status_code == 401


class TestStatusSideEffects:
    """Tests for status change side effects."""

    async def test_resolved_sets_resolved_at(
        self, client: AsyncClient, support_token: str, db_session, ticket
    ):
        """Resolving a ticket should set resolved_at timestamp."""
        from app.models.ticket import TicketStatus

        ticket.status = TicketStatus.IN_PROGRESS
        await db_session.commit()

        response = await client.patch(
            f"/api/v1/tickets/{ticket.id}/status",
            json={"status": "RESOLVED", "comment": "Fixed"},
            headers=auth_headers(support_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["resolved_at"] is not None

    async def test_status_change_with_comment(
        self, client: AsyncClient, support_token: str, ticket
    ):
        """Status changes can include a comment."""
        response = await client.patch(
            f"/api/v1/tickets/{ticket.id}/status",
            json={"status": "IN_PROGRESS", "comment": "Starting to work on this issue"},
            headers=auth_headers(support_token),
        )
        assert response.status_code == 200

    async def test_nonexistent_ticket_returns_404(
        self, client: AsyncClient, support_token: str
    ):
        """Should return 404 for nonexistent ticket."""
        response = await client.patch(
            f"/api/v1/tickets/{uuid.uuid4()}/status",
            json={"status": "IN_PROGRESS"},
            headers=auth_headers(support_token),
        )
        assert response.status_code == 404
