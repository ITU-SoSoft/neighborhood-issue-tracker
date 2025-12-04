"""Tests for user management endpoints."""

import pytest
from httpx import AsyncClient

from app.models import User, UserRole


class TestListUsers:
    """Tests for GET /api/v1/users/."""

    async def test_list_users_as_manager(
        self, client: AsyncClient, manager_user: User, manager_token: str
    ):
        """Manager should be able to list all users."""
        response = await client.get(
            "/api/v1/users/",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        # Response is paginated
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert len(data["items"]) >= 1

    async def test_list_users_as_support(
        self, client: AsyncClient, support_user: User, support_token: str
    ):
        """Support user should not be able to list users."""
        response = await client.get(
            "/api/v1/users/",
            headers={"Authorization": f"Bearer {support_token}"},
        )
        assert response.status_code == 403

    async def test_list_users_as_citizen(
        self, client: AsyncClient, citizen_user: User, citizen_token: str
    ):
        """Citizen should not be able to list users."""
        response = await client.get(
            "/api/v1/users/",
            headers={"Authorization": f"Bearer {citizen_token}"},
        )
        assert response.status_code == 403

    async def test_list_users_unauthenticated(self, client: AsyncClient):
        """Unauthenticated request should be rejected."""
        response = await client.get("/api/v1/users/")
        assert response.status_code == 401


class TestGetUser:
    """Tests for GET /api/v1/users/{user_id}."""

    async def test_get_own_user(
        self, client: AsyncClient, citizen_user: User, citizen_token: str
    ):
        """User should be able to get their own profile."""
        response = await client.get(
            f"/api/v1/users/{citizen_user.id}",
            headers={"Authorization": f"Bearer {citizen_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(citizen_user.id)
        assert data["phone_number"] == citizen_user.phone_number

    async def test_get_other_user_as_citizen(
        self,
        client: AsyncClient,
        citizen_user: User,
        support_user: User,
        citizen_token: str,
    ):
        """Citizen should not be able to get another user's profile."""
        response = await client.get(
            f"/api/v1/users/{support_user.id}",
            headers={"Authorization": f"Bearer {citizen_token}"},
        )
        assert response.status_code == 403

    async def test_get_other_user_as_manager(
        self,
        client: AsyncClient,
        manager_user: User,
        citizen_user: User,
        manager_token: str,
    ):
        """Manager should be able to get any user's profile."""
        response = await client.get(
            f"/api/v1/users/{citizen_user.id}",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(citizen_user.id)


class TestUpdateUser:
    """Tests for PUT /api/v1/users/{user_id}."""

    async def test_update_own_profile(
        self, client: AsyncClient, citizen_user: User, citizen_token: str
    ):
        """User should be able to update their own profile."""
        response = await client.put(
            f"/api/v1/users/{citizen_user.id}",
            headers={"Authorization": f"Bearer {citizen_token}"},
            json={"name": "Updated Name", "email": "updated@example.com"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["email"] == "updated@example.com"

    async def test_update_other_user_profile(
        self,
        client: AsyncClient,
        citizen_user: User,
        support_user: User,
        citizen_token: str,
    ):
        """User should not be able to update another user's profile."""
        response = await client.put(
            f"/api/v1/users/{support_user.id}",
            headers={"Authorization": f"Bearer {citizen_token}"},
            json={"name": "Hacked Name"},
        )
        assert response.status_code == 403


class TestUpdateUserRole:
    """Tests for PATCH /api/v1/users/{user_id}/role."""

    async def test_update_role_as_manager(
        self,
        client: AsyncClient,
        citizen_user: User,
        manager_user: User,
        manager_token: str,
    ):
        """Manager should be able to update user role."""
        response = await client.patch(
            f"/api/v1/users/{citizen_user.id}/role",
            headers={"Authorization": f"Bearer {manager_token}"},
            json={"role": "support"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "support"

    async def test_update_role_as_support(
        self,
        client: AsyncClient,
        citizen_user: User,
        support_user: User,
        support_token: str,
    ):
        """Support user should not be able to update roles."""
        response = await client.patch(
            f"/api/v1/users/{citizen_user.id}/role",
            headers={"Authorization": f"Bearer {support_token}"},
            json={"role": "manager"},
        )
        assert response.status_code == 403

    async def test_update_role_invalid_role(
        self,
        client: AsyncClient,
        citizen_user: User,
        manager_token: str,
    ):
        """Should reject invalid role value."""
        response = await client.patch(
            f"/api/v1/users/{citizen_user.id}/role",
            headers={"Authorization": f"Bearer {manager_token}"},
            json={"role": "admin"},  # Invalid role
        )
        assert response.status_code == 422


class TestDeleteUser:
    """Tests for DELETE /api/v1/users/{user_id}."""

    async def test_delete_user_as_manager(
        self,
        client: AsyncClient,
        citizen_user: User,
        manager_user: User,
        manager_token: str,
    ):
        """Manager should be able to soft delete a user."""
        response = await client.delete(
            f"/api/v1/users/{citizen_user.id}",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        # DELETE returns 204 No Content on success
        assert response.status_code == 204

    async def test_delete_user_as_citizen(
        self,
        client: AsyncClient,
        support_user: User,
        citizen_user: User,
        citizen_token: str,
    ):
        """Citizen should not be able to delete users."""
        response = await client.delete(
            f"/api/v1/users/{support_user.id}",
            headers={"Authorization": f"Bearer {citizen_token}"},
        )
        assert response.status_code == 403
