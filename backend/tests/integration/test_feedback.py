"""Integration tests for Feedback API endpoints."""

import uuid

from httpx import AsyncClient

from tests.conftest import auth_headers


# ============================================================================
# POST /api/v1/feedback/tickets/{id} - Create feedback
# ============================================================================


class TestCreateFeedback:
    """Tests for POST /api/v1/feedback/tickets/{id}."""

    async def test_citizen_creates_feedback_on_resolved_ticket(
        self, client: AsyncClient, citizen_token: str, db_session, ticket
    ):
        """Citizen should be able to give feedback on resolved tickets."""
        from app.models.ticket import TicketStatus

        ticket.status = TicketStatus.RESOLVED
        await db_session.commit()

        response = await client.post(
            f"/api/v1/feedback/tickets/{ticket.id}",
            json={"rating": 5, "comment": "Great job fixing this issue!"},
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 201
        data = response.json()
        assert data["rating"] == 5
        assert data["comment"] == "Great job fixing this issue!"

    async def test_rating_validation_min(
        self, client: AsyncClient, citizen_token: str, db_session, ticket
    ):
        """Rating must be at least 1."""
        from app.models.ticket import TicketStatus

        ticket.status = TicketStatus.RESOLVED
        await db_session.commit()

        response = await client.post(
            f"/api/v1/feedback/tickets/{ticket.id}",
            json={"rating": 0},  # Invalid: less than 1
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 422

    async def test_rating_validation_max(
        self, client: AsyncClient, citizen_token: str, db_session, ticket
    ):
        """Rating must be at most 5."""
        from app.models.ticket import TicketStatus

        ticket.status = TicketStatus.RESOLVED
        await db_session.commit()

        response = await client.post(
            f"/api/v1/feedback/tickets/{ticket.id}",
            json={"rating": 6},  # Invalid: greater than 5
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 422

    async def test_feedback_without_comment(
        self, client: AsyncClient, citizen_token: str, db_session, ticket
    ):
        """Feedback should be allowed without a comment."""
        from app.models.ticket import TicketStatus

        ticket.status = TicketStatus.RESOLVED
        await db_session.commit()

        response = await client.post(
            f"/api/v1/feedback/tickets/{ticket.id}",
            json={"rating": 4},
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 201
        data = response.json()
        assert data["rating"] == 4

    async def test_cannot_give_feedback_on_new_ticket(
        self, client: AsyncClient, citizen_token: str, ticket
    ):
        """Should not allow feedback on NEW tickets."""
        response = await client.post(
            f"/api/v1/feedback/tickets/{ticket.id}",
            json={"rating": 5},
            headers=auth_headers(citizen_token),
        )
        # Should fail - ticket not resolved/closed
        assert response.status_code in [400, 403, 422]

    async def test_only_reporter_can_give_feedback(
        self, client: AsyncClient, support_token: str, db_session, ticket
    ):
        """Only the ticket reporter should be able to give feedback."""
        from app.models.ticket import TicketStatus

        ticket.status = TicketStatus.RESOLVED
        await db_session.commit()

        response = await client.post(
            f"/api/v1/feedback/tickets/{ticket.id}",
            json={"rating": 3},
            headers=auth_headers(support_token),
        )
        # Support user is not the reporter
        assert response.status_code == 403

    async def test_nonexistent_ticket_returns_404(
        self, client: AsyncClient, citizen_token: str
    ):
        """Should return 404 for nonexistent ticket."""
        response = await client.post(
            f"/api/v1/feedback/tickets/{uuid.uuid4()}",
            json={"rating": 5},
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 404


# ============================================================================
# GET /api/v1/feedback/tickets/{id} - Get feedback
# ============================================================================


class TestGetFeedback:
    """Tests for GET /api/v1/feedback/tickets/{id}."""

    async def test_get_ticket_feedback(
        self, client: AsyncClient, citizen_token: str, db_session, ticket
    ):
        """Should return feedback for a ticket if exists."""
        from app.models.ticket import TicketStatus
        from app.models.feedback import Feedback

        ticket.status = TicketStatus.RESOLVED
        await db_session.flush()

        # Create feedback
        feedback = Feedback(
            id=uuid.uuid4(),
            ticket_id=ticket.id,
            user_id=ticket.reporter_id,
            rating=4,
            comment="Good work",
        )
        db_session.add(feedback)
        await db_session.commit()

        response = await client.get(
            f"/api/v1/feedback/tickets/{ticket.id}",
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["rating"] == 4
        assert data["comment"] == "Good work"

    async def test_no_feedback_returns_404(
        self, client: AsyncClient, citizen_token: str, ticket
    ):
        """Should return 404 when no feedback exists for ticket."""
        response = await client.get(
            f"/api/v1/feedback/tickets/{ticket.id}",
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 404
