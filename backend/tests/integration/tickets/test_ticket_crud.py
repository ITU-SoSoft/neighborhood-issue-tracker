"""Integration tests for Ticket CRUD API endpoints."""

import uuid

from httpx import AsyncClient

from tests.conftest import auth_headers


# ============================================================================
# POST /api/v1/tickets - Create ticket
# ============================================================================


class TestCreateTicket:
    """Tests for POST /api/v1/tickets."""

    async def test_citizen_creates_ticket_successfully(
        self, client: AsyncClient, citizen_token: str, category
    ):
        """Citizen should be able to create a ticket."""
        response = await client.post(
            "/api/v1/tickets/",
            json={
                "title": "Pothole on Main Street",
                "description": "There is a large pothole that needs to be fixed urgently.",
                "category_id": str(category.id),
                "location": {
                    "latitude": 41.0082,
                    "longitude": 28.9784,
                    "address": "Main Street 123",
                    "city": "Istanbul",
                },
            },
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Pothole on Main Street"
        assert data["status"] == "NEW"
        assert data["category_id"] == str(category.id)

    async def test_create_ticket_with_gps_coordinates(
        self, client: AsyncClient, citizen_token: str, category
    ):
        """Should create ticket using GPS coordinates."""
        response = await client.post(
            "/api/v1/tickets/",
            json={
                "title": "Street Light Not Working",
                "description": "The street light on the corner has been broken for a week.",
                "category_id": str(category.id),
                "location": {
                    "latitude": 41.0500,
                    "longitude": 29.0300,
                    "address": "Corner of 5th and Oak",
                    "city": "Istanbul",
                },
            },
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 201
        data = response.json()
        assert data["location"]["latitude"] == 41.05
        assert data["location"]["longitude"] == 29.03

    async def test_create_ticket_inactive_category_fails(
        self, client: AsyncClient, citizen_token: str, db_session
    ):
        """Should fail when trying to use an inactive category."""
        from app.models.category import Category

        # Create an inactive category
        inactive_category = Category(
            id=uuid.uuid4(),
            name="Inactive Category",
            is_active=False,
        )
        db_session.add(inactive_category)
        await db_session.commit()

        response = await client.post(
            "/api/v1/tickets/",
            json={
                "title": "Test Ticket Title",
                "description": "This is a test ticket with an inactive category.",
                "category_id": str(inactive_category.id),
                "location": {
                    "latitude": 41.0082,
                    "longitude": 28.9784,
                    "city": "Istanbul",
                },
            },
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 404

    async def test_create_ticket_nonexistent_category_fails(
        self, client: AsyncClient, citizen_token: str
    ):
        """Should fail when category doesn't exist."""
        response = await client.post(
            "/api/v1/tickets/",
            json={
                "title": "Test Ticket Title",
                "description": "This is a test ticket with a nonexistent category.",
                "category_id": str(uuid.uuid4()),
                "location": {
                    "latitude": 41.0082,
                    "longitude": 28.9784,
                    "city": "Istanbul",
                },
            },
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 404

    async def test_create_ticket_title_validation(
        self, client: AsyncClient, citizen_token: str, category
    ):
        """Should validate title length."""
        # Too short title
        response = await client.post(
            "/api/v1/tickets/",
            json={
                "title": "Hi",  # Less than 5 characters
                "description": "This is a valid description that is long enough.",
                "category_id": str(category.id),
                "location": {
                    "latitude": 41.0082,
                    "longitude": 28.9784,
                    "city": "Istanbul",
                },
            },
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 422

    async def test_create_ticket_description_validation(
        self, client: AsyncClient, citizen_token: str, category
    ):
        """Should validate description length."""
        # Too short description
        response = await client.post(
            "/api/v1/tickets/",
            json={
                "title": "Valid Title Here",
                "description": "Short",  # Less than 10 characters
                "category_id": str(category.id),
                "location": {
                    "latitude": 41.0082,
                    "longitude": 28.9784,
                    "city": "Istanbul",
                },
            },
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 422

    async def test_create_ticket_location_required(
        self, client: AsyncClient, citizen_token: str, category
    ):
        """Should require location with latitude/longitude."""
        response = await client.post(
            "/api/v1/tickets/",
            json={
                "title": "Valid Title Here",
                "description": "This is a valid description that is long enough.",
                "category_id": str(category.id),
                # No location at all
            },
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 422

    async def test_unauthenticated_cannot_create_ticket(
        self, client: AsyncClient, category
    ):
        """Unauthenticated requests should be rejected."""
        response = await client.post(
            "/api/v1/tickets/",
            json={
                "title": "Test Ticket Title",
                "description": "This is a test ticket description.",
                "category_id": str(category.id),
                "location": {
                    "latitude": 41.0082,
                    "longitude": 28.9784,
                    "city": "Istanbul",
                },
            },
        )
        assert response.status_code == 401


# ============================================================================
# GET /api/v1/tickets - List tickets
# ============================================================================


class TestListTickets:
    """Tests for GET /api/v1/tickets."""

    async def test_support_lists_all_tickets(
        self, client: AsyncClient, support_token: str, ticket
    ):
        """Support user should be able to list all tickets."""
        response = await client.get(
            "/api/v1/tickets/",
            headers=auth_headers(support_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1

    async def test_manager_lists_all_tickets(
        self, client: AsyncClient, manager_token: str, ticket
    ):
        """Manager should be able to list all tickets."""
        response = await client.get(
            "/api/v1/tickets/",
            headers=auth_headers(manager_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    async def test_citizen_cannot_list_all_tickets(
        self, client: AsyncClient, citizen_token: str
    ):
        """Citizen should not be able to access the list tickets endpoint."""
        response = await client.get(
            "/api/v1/tickets/",
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 403

    async def test_filter_by_status(
        self, client: AsyncClient, support_token: str, ticket
    ):
        """Should be able to filter tickets by status."""
        response = await client.get(
            "/api/v1/tickets/?status_filter=NEW",
            headers=auth_headers(support_token),
        )
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["status"] == "NEW"

    async def test_filter_by_category(
        self, client: AsyncClient, support_token: str, ticket, category
    ):
        """Should be able to filter tickets by category."""
        response = await client.get(
            f"/api/v1/tickets/?category_id={category.id}",
            headers=auth_headers(support_token),
        )
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["category_id"] == str(category.id)

    async def test_pagination(self, client: AsyncClient, support_token: str, ticket):
        """Should support pagination."""
        response = await client.get(
            "/api/v1/tickets/?page=1&page_size=10",
            headers=auth_headers(support_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 10


# ============================================================================
# GET /api/v1/tickets/{id} - Get single ticket
# ============================================================================


class TestGetTicket:
    """Tests for GET /api/v1/tickets/{id}."""

    async def test_citizen_gets_own_ticket(
        self, client: AsyncClient, citizen_token: str, ticket, citizen_user
    ):
        """Citizen should be able to get their own ticket details."""
        response = await client.get(
            f"/api/v1/tickets/{ticket.id}",
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(ticket.id)
        assert data["title"] == ticket.title

    async def test_citizen_gets_other_ticket(
        self, client: AsyncClient, citizen_token: str, db_session, category
    ):
        """Citizen should be able to view other users' tickets (public view)."""
        from app.models.user import User, UserRole
        from app.models.ticket import Ticket, Location, TicketStatus

        # Create another user and their ticket
        other_user = User(
            id=uuid.uuid4(),
            phone_number="+905559999999",
            email="other_user@test.com",
            password_hash="dummy_hash",
            name="Other User",
            role=UserRole.CITIZEN,
            is_verified=True,
            is_active=True,
        )
        db_session.add(other_user)
        await db_session.flush()

        location = Location(
            id=uuid.uuid4(),
            latitude=41.0,
            longitude=29.0,
            coordinates="SRID=4326;POINT(29.0 41.0)",
            city="Istanbul",
        )
        db_session.add(location)
        await db_session.flush()

        other_ticket = Ticket(
            id=uuid.uuid4(),
            title="Other User Ticket",
            description="Another user's issue",
            status=TicketStatus.NEW,
            category_id=category.id,
            location_id=location.id,
            reporter_id=other_user.id,
        )
        db_session.add(other_ticket)
        await db_session.commit()

        # Use existing citizen_token to view the other ticket
        response = await client.get(
            f"/api/v1/tickets/{other_ticket.id}",
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 200

    async def test_support_gets_any_ticket(
        self, client: AsyncClient, support_token: str, ticket
    ):
        """Support user should be able to get any ticket details."""
        response = await client.get(
            f"/api/v1/tickets/{ticket.id}",
            headers=auth_headers(support_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(ticket.id)

    async def test_nonexistent_ticket_returns_404(
        self, client: AsyncClient, citizen_token: str
    ):
        """Should return 404 for nonexistent ticket."""
        response = await client.get(
            f"/api/v1/tickets/{uuid.uuid4()}",
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 404


# ============================================================================
# PATCH /api/v1/tickets/{id} - Update ticket
# ============================================================================


class TestUpdateTicket:
    """Tests for PATCH /api/v1/tickets/{id}."""

    async def test_citizen_updates_own_new_ticket(
        self, client: AsyncClient, citizen_token: str, ticket
    ):
        """Citizen should be able to update their own NEW ticket."""
        response = await client.patch(
            f"/api/v1/tickets/{ticket.id}",
            json={"title": "Updated Ticket Title"},
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Ticket Title"

    async def test_citizen_cannot_update_in_progress_ticket(
        self, client: AsyncClient, citizen_token: str, db_session, ticket
    ):
        """Citizen should not be able to update IN_PROGRESS tickets."""
        from app.models.ticket import TicketStatus

        ticket.status = TicketStatus.IN_PROGRESS
        await db_session.commit()

        response = await client.patch(
            f"/api/v1/tickets/{ticket.id}",
            json={"title": "Try to Update"},
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 403

    async def test_support_updates_any_ticket(
        self, client: AsyncClient, support_token: str, db_session, ticket
    ):
        """Support user should be able to update any non-closed ticket."""
        from app.models.ticket import TicketStatus

        ticket.status = TicketStatus.IN_PROGRESS
        await db_session.commit()

        response = await client.patch(
            f"/api/v1/tickets/{ticket.id}",
            json={"description": "Updated description by support staff member"},
            headers=auth_headers(support_token),
        )
        assert response.status_code == 200

    async def test_cannot_update_closed_ticket(
        self, client: AsyncClient, support_token: str, db_session, ticket
    ):
        """No one should be able to update a CLOSED ticket."""
        from app.models.ticket import TicketStatus

        ticket.status = TicketStatus.CLOSED
        await db_session.commit()

        response = await client.patch(
            f"/api/v1/tickets/{ticket.id}",
            json={"title": "Try to Update Closed"},
            headers=auth_headers(support_token),
        )
        assert response.status_code == 403

    async def test_update_with_invalid_category_fails(
        self, client: AsyncClient, citizen_token: str, ticket
    ):
        """Should fail when updating to an invalid category."""
        response = await client.patch(
            f"/api/v1/tickets/{ticket.id}",
            json={"category_id": str(uuid.uuid4())},
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 404
