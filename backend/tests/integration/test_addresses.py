"""Integration tests for Address API endpoints."""

import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SavedAddress, User
from tests.conftest import auth_headers


class TestListAddresses:
    """Tests for GET /api/v1/addresses."""

    async def test_list_addresses_empty(self, client: AsyncClient, citizen_token: str):
        """User with no addresses should get empty list."""
        response = await client.get(
            "/api/v1/addresses",
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    async def test_list_addresses_with_addresses(
        self,
        client: AsyncClient,
        citizen_token: str,
        db_session: AsyncSession,
        citizen_user: User,
    ):
        """User should see their saved addresses."""
        # Create an address for the user
        address = SavedAddress(
            id=uuid.uuid4(),
            user_id=citizen_user.id,
            name="Home",
            address="123 Main St",
            city="Istanbul",
            latitude=41.0082,
            longitude=28.9784,
        )
        db_session.add(address)
        await db_session.commit()

        response = await client.get(
            "/api/v1/addresses",
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["total"] == 1
        assert data["items"][0]["name"] == "Home"

    async def test_list_addresses_unauthenticated(self, client: AsyncClient):
        """Unauthenticated user should not be able to list addresses."""
        response = await client.get("/api/v1/addresses")
        assert response.status_code == 401


class TestCreateAddress:
    """Tests for POST /api/v1/addresses."""

    async def test_create_address(self, client: AsyncClient, citizen_token: str):
        """User should be able to save an address."""
        response = await client.post(
            "/api/v1/addresses",
            json={
                "name": "Home",
                "address": "123 Main St",
                "city": "Istanbul",
                "latitude": 41.0082,
                "longitude": 28.9784,
            },
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Home"
        assert data["address"] == "123 Main St"
        assert data["city"] == "Istanbul"
        assert "id" in data

    async def test_create_duplicate_name(
        self,
        client: AsyncClient,
        citizen_token: str,
        db_session: AsyncSession,
        citizen_user: User,
    ):
        """Should reject duplicate address names for same user."""
        # Create an address first
        address = SavedAddress(
            id=uuid.uuid4(),
            user_id=citizen_user.id,
            name="Office",
            address="456 Work Ave",
            city="Istanbul",
            latitude=41.01,
            longitude=28.98,
        )
        db_session.add(address)
        await db_session.commit()

        # Try to create another with same name
        response = await client.post(
            "/api/v1/addresses",
            json={
                "name": "Office",
                "address": "789 Other Rd",
                "city": "Istanbul",
                "latitude": 41.02,
                "longitude": 28.99,
            },
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    async def test_create_address_max_limit(
        self,
        client: AsyncClient,
        citizen_token: str,
        db_session: AsyncSession,
        citizen_user: User,
    ):
        """Should reject when user reaches max 10 addresses."""
        # Create 10 addresses
        for i in range(10):
            address = SavedAddress(
                id=uuid.uuid4(),
                user_id=citizen_user.id,
                name=f"Address {i}",
                address=f"{i} Street",
                city="Istanbul",
                latitude=41.0 + i * 0.01,
                longitude=28.9 + i * 0.01,
            )
            db_session.add(address)
        await db_session.commit()

        # Try to create 11th
        response = await client.post(
            "/api/v1/addresses",
            json={
                "name": "Too Many",
                "address": "11 Street",
                "city": "Istanbul",
                "latitude": 41.11,
                "longitude": 28.99,
            },
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 400
        assert "Maximum" in response.json()["detail"]


class TestGetAddress:
    """Tests for GET /api/v1/addresses/{address_id}."""

    async def test_get_address(
        self,
        client: AsyncClient,
        citizen_token: str,
        db_session: AsyncSession,
        citizen_user: User,
    ):
        """User should be able to get a specific address."""
        address = SavedAddress(
            id=uuid.uuid4(),
            user_id=citizen_user.id,
            name="My Place",
            address="123 Street",
            city="Istanbul",
            latitude=41.01,
            longitude=28.98,
        )
        db_session.add(address)
        await db_session.commit()

        response = await client.get(
            f"/api/v1/addresses/{address.id}",
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "My Place"
        assert data["id"] == str(address.id)

    async def test_get_address_not_found(self, client: AsyncClient, citizen_token: str):
        """Should return 404 for nonexistent address."""
        fake_id = uuid.uuid4()
        response = await client.get(
            f"/api/v1/addresses/{fake_id}",
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 404

    async def test_get_other_users_address(
        self,
        client: AsyncClient,
        citizen_token: str,
        db_session: AsyncSession,
        support_user: User,
    ):
        """User should not be able to get another user's address."""
        # Create an address for support_user
        address = SavedAddress(
            id=uuid.uuid4(),
            user_id=support_user.id,
            name="Not Mine",
            address="999 Other St",
            city="Istanbul",
            latitude=41.01,
            longitude=28.98,
        )
        db_session.add(address)
        await db_session.commit()

        # Try to access as citizen
        response = await client.get(
            f"/api/v1/addresses/{address.id}",
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 404


class TestUpdateAddress:
    """Tests for PUT /api/v1/addresses/{address_id}."""

    async def test_update_address(
        self,
        client: AsyncClient,
        citizen_token: str,
        db_session: AsyncSession,
        citizen_user: User,
    ):
        """User should be able to update an address."""
        address = SavedAddress(
            id=uuid.uuid4(),
            user_id=citizen_user.id,
            name="Old Name",
            address="123 Street",
            city="Istanbul",
            latitude=41.01,
            longitude=28.98,
        )
        db_session.add(address)
        await db_session.commit()

        response = await client.put(
            f"/api/v1/addresses/{address.id}",
            json={"name": "New Name"},
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 200
        assert response.json()["name"] == "New Name"

    async def test_update_address_not_found(
        self, client: AsyncClient, citizen_token: str
    ):
        """Should return 404 for nonexistent address."""
        fake_id = uuid.uuid4()
        response = await client.put(
            f"/api/v1/addresses/{fake_id}",
            json={"name": "New Name"},
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 404

    async def test_update_address_duplicate_name(
        self,
        client: AsyncClient,
        citizen_token: str,
        db_session: AsyncSession,
        citizen_user: User,
    ):
        """Should reject update if new name already exists."""
        # Create two addresses
        addr1 = SavedAddress(
            id=uuid.uuid4(),
            user_id=citizen_user.id,
            name="First",
            address="1 Street",
            city="Istanbul",
            latitude=41.01,
            longitude=28.98,
        )
        addr2 = SavedAddress(
            id=uuid.uuid4(),
            user_id=citizen_user.id,
            name="Second",
            address="2 Street",
            city="Istanbul",
            latitude=41.02,
            longitude=28.99,
        )
        db_session.add_all([addr1, addr2])
        await db_session.commit()

        # Try to rename Second to First
        response = await client.put(
            f"/api/v1/addresses/{addr2.id}",
            json={"name": "First"},
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]


class TestDeleteAddress:
    """Tests for DELETE /api/v1/addresses/{address_id}."""

    async def test_delete_address(
        self,
        client: AsyncClient,
        citizen_token: str,
        db_session: AsyncSession,
        citizen_user: User,
    ):
        """User should be able to delete an address."""
        address = SavedAddress(
            id=uuid.uuid4(),
            user_id=citizen_user.id,
            name="To Delete",
            address="123 Street",
            city="Istanbul",
            latitude=41.01,
            longitude=28.98,
        )
        db_session.add(address)
        await db_session.commit()

        response = await client.delete(
            f"/api/v1/addresses/{address.id}",
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 204

    async def test_delete_address_not_found(
        self, client: AsyncClient, citizen_token: str
    ):
        """Should return 404 for nonexistent address."""
        fake_id = uuid.uuid4()
        response = await client.delete(
            f"/api/v1/addresses/{fake_id}",
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 404
