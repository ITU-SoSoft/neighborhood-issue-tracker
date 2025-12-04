"""Tests for category endpoints."""

import pytest
from httpx import AsyncClient

from app.models import Category, User


class TestListCategories:
    """Tests for GET /api/v1/categories/."""

    async def test_list_categories_unauthenticated(
        self, client: AsyncClient, categories: list[Category]
    ):
        """Categories should be publicly accessible."""
        response = await client.get("/api/v1/categories/")
        assert response.status_code == 200
        data = response.json()
        # Response is paginated with items and total
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) == len(categories)
        assert data["total"] == len(categories)

    async def test_list_categories_authenticated(
        self, client: AsyncClient, categories: list[Category], citizen_token: str
    ):
        """Authenticated user can list categories."""
        response = await client.get(
            "/api/v1/categories/",
            headers={"Authorization": f"Bearer {citizen_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        # Response is paginated with items and total
        assert "items" in data
        assert len(data["items"]) == len(categories)


class TestGetCategory:
    """Tests for GET /api/v1/categories/{category_id}."""

    async def test_get_category(self, client: AsyncClient, category: Category):
        """Should return category by ID."""
        response = await client.get(f"/api/v1/categories/{category.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(category.id)
        assert data["name"] == category.name

    async def test_get_nonexistent_category(self, client: AsyncClient):
        """Should return 404 for nonexistent category."""
        import uuid

        fake_id = uuid.uuid4()
        response = await client.get(f"/api/v1/categories/{fake_id}")
        assert response.status_code == 404


class TestCreateCategory:
    """Tests for POST /api/v1/categories/."""

    async def test_create_category_as_manager(
        self, client: AsyncClient, manager_user: User, manager_token: str
    ):
        """Manager should be able to create categories."""
        response = await client.post(
            "/api/v1/categories/",
            headers={"Authorization": f"Bearer {manager_token}"},
            json={"name": "New Category", "description": "Test description"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Category"
        assert data["description"] == "Test description"
        assert data["is_active"] is True

    async def test_create_category_as_support(
        self, client: AsyncClient, support_user: User, support_token: str
    ):
        """Support user should not be able to create categories."""
        response = await client.post(
            "/api/v1/categories/",
            headers={"Authorization": f"Bearer {support_token}"},
            json={"name": "Unauthorized Category"},
        )
        assert response.status_code == 403

    async def test_create_category_as_citizen(
        self, client: AsyncClient, citizen_user: User, citizen_token: str
    ):
        """Citizen should not be able to create categories."""
        response = await client.post(
            "/api/v1/categories/",
            headers={"Authorization": f"Bearer {citizen_token}"},
            json={"name": "Unauthorized Category"},
        )
        assert response.status_code == 403

    async def test_create_duplicate_category(
        self, client: AsyncClient, category: Category, manager_token: str
    ):
        """Should reject duplicate category names."""
        response = await client.post(
            "/api/v1/categories/",
            headers={"Authorization": f"Bearer {manager_token}"},
            json={"name": category.name},
        )
        assert response.status_code == 409


class TestUpdateCategory:
    """Tests for PUT /api/v1/categories/{category_id}."""

    async def test_update_category_as_manager(
        self, client: AsyncClient, category: Category, manager_token: str
    ):
        """Manager should be able to update categories."""
        response = await client.put(
            f"/api/v1/categories/{category.id}",
            headers={"Authorization": f"Bearer {manager_token}"},
            json={"name": "Updated Category", "description": "Updated description"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Category"
        assert data["description"] == "Updated description"

    async def test_update_category_as_citizen(
        self, client: AsyncClient, category: Category, citizen_token: str
    ):
        """Citizen should not be able to update categories."""
        response = await client.put(
            f"/api/v1/categories/{category.id}",
            headers={"Authorization": f"Bearer {citizen_token}"},
            json={"name": "Hacked Category"},
        )
        assert response.status_code == 403

    async def test_update_nonexistent_category(
        self, client: AsyncClient, manager_token: str
    ):
        """Should return 404 for nonexistent category."""
        import uuid

        fake_id = uuid.uuid4()
        response = await client.put(
            f"/api/v1/categories/{fake_id}",
            headers={"Authorization": f"Bearer {manager_token}"},
            json={"name": "Updated"},
        )
        assert response.status_code == 404

    async def test_deactivate_category(
        self, client: AsyncClient, category: Category, manager_token: str
    ):
        """Manager should be able to deactivate categories."""
        response = await client.put(
            f"/api/v1/categories/{category.id}",
            headers={"Authorization": f"Bearer {manager_token}"},
            json={"is_active": False},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False
