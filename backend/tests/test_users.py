"""Tests for user management endpoints."""

import uuid

from httpx import AsyncClient

from app.models import User
from app.models.team import Team
from app.models.user import UserRole


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
            json={"role": "SUPPORT"},  # Role must be uppercase
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "SUPPORT"

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


# ============================================================================
# Additional tests for improved coverage
# ============================================================================


class TestListUsersFiltering:
    """Additional tests for GET /api/v1/users/ with filters."""

    async def test_list_users_filter_by_role(
        self,
        client: AsyncClient,
        manager_user: User,
        support_user: User,
        citizen_user: User,
        manager_token: str,
    ):
        """Should filter users by role."""
        response = await client.get(
            "/api/v1/users/",
            params={"role": "SUPPORT"},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        # All returned users should be SUPPORT role
        for user in data["items"]:
            assert user["role"] == "SUPPORT"

    async def test_list_users_filter_by_team_id(
        self,
        client: AsyncClient,
        manager_user: User,
        support_user_with_team: User,
        team: "Team",
        manager_token: str,
    ):
        """Should filter users by team_id."""
        response = await client.get(
            "/api/v1/users/",
            params={"team_id": str(team.id)},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        # All returned users should be in the specified team
        for user in data["items"]:
            assert user["team_id"] == str(team.id)

    async def test_list_users_pagination(
        self,
        client: AsyncClient,
        manager_user: User,
        manager_token: str,
        db_session,
    ):
        """Should paginate results correctly."""
        # Create additional users for pagination testing
        from app.models.user import User as UserModel
        import uuid

        for i in range(5):
            user = UserModel(
                id=uuid.uuid4(),
                phone_number=f"+90555999{i:04d}",
                name=f"Pagination User {i}",
                email=f"pagination{i}@test.com",
                password_hash="hashed_password",
                role=UserRole.CITIZEN,
                is_verified=True,
                is_active=True,
            )
            db_session.add(user)
        await db_session.commit()

        # Request page 1 with page_size 2
        response = await client.get(
            "/api/v1/users/",
            params={"page": 1, "page_size": 2},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["total"] >= 5


class TestUpdateUserAdditional:
    """Additional tests for PUT /api/v1/users/{user_id}."""

    async def test_update_user_duplicate_phone_fails(
        self,
        client: AsyncClient,
        citizen_user: User,
        support_user: User,
        citizen_token: str,
    ):
        """Should reject update with duplicate phone number."""
        # Try to update citizen's phone to support's phone
        response = await client.put(
            f"/api/v1/users/{citizen_user.id}",
            headers={"Authorization": f"Bearer {citizen_token}"},
            json={"phone_number": support_user.phone_number},
        )
        assert response.status_code == 400
        data = response.json()
        assert "phone" in data["detail"].lower() or "use" in data["detail"].lower()

    async def test_update_user_partial_update(
        self,
        client: AsyncClient,
        citizen_user: User,
        citizen_token: str,
    ):
        """Should allow partial updates (only name, not email)."""
        original_email = citizen_user.email
        response = await client.put(
            f"/api/v1/users/{citizen_user.id}",
            headers={"Authorization": f"Bearer {citizen_token}"},
            json={"name": "Only Name Updated"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Only Name Updated"
        # Email should remain unchanged
        assert data["email"] == original_email


class TestUpdateUserRoleAdditional:
    """Additional tests for PATCH /api/v1/users/{user_id}/role."""

    async def test_update_role_with_team_assignment(
        self,
        client: AsyncClient,
        citizen_user: User,
        team: "Team",
        manager_token: str,
    ):
        """Should assign user to team along with role change."""
        response = await client.patch(
            f"/api/v1/users/{citizen_user.id}/role",
            headers={"Authorization": f"Bearer {manager_token}"},
            json={"role": "SUPPORT", "team_id": str(team.id)},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "SUPPORT"
        assert data["team_id"] == str(team.id)

    async def test_update_role_nonexistent_user(
        self,
        client: AsyncClient,
        manager_token: str,
    ):
        """Should return 404 for non-existent user."""

        response = await client.patch(
            f"/api/v1/users/{uuid.uuid4()}/role",
            headers={"Authorization": f"Bearer {manager_token}"},
            json={"role": "SUPPORT"},
        )
        assert response.status_code == 404


class TestDeleteUserAdditional:
    """Additional tests for DELETE /api/v1/users/{user_id}."""

    async def test_delete_user_soft_delete_verification(
        self,
        client: AsyncClient,
        db_session,
        manager_token: str,
    ):
        """Verify that deleted user is soft deleted (not hard deleted)."""
        from app.models.user import User as UserModel
        from sqlalchemy import select
        import uuid

        # Create a user to delete
        user_id = uuid.uuid4()
        user = UserModel(
            id=user_id,
            phone_number="+905559998877",
            name="To Be Deleted",
            email="delete_me@test.com",
            password_hash="hashed_password",
            role=UserRole.CITIZEN,
            is_verified=True,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

        # Delete the user
        response = await client.delete(
            f"/api/v1/users/{user_id}",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert response.status_code == 204

        # Verify user still exists in DB but has deleted_at set
        result = await db_session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        deleted_user = result.scalar_one_or_none()
        assert deleted_user is not None
        assert deleted_user.deleted_at is not None

    async def test_delete_nonexistent_user(
        self,
        client: AsyncClient,
        manager_token: str,
    ):
        """Should return 404 for non-existent user."""

        response = await client.delete(
            f"/api/v1/users/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert response.status_code == 404

    async def test_get_deleted_user_returns_404(
        self,
        client: AsyncClient,
        db_session,
        manager_token: str,
    ):
        """Deleted user should not be retrievable."""
        from app.models.user import User as UserModel
        from datetime import datetime, timezone
        import uuid

        # Create a soft-deleted user
        user_id = uuid.uuid4()
        user = UserModel(
            id=user_id,
            phone_number="+905559997766",
            name="Already Deleted",
            email="already_deleted@test.com",
            password_hash="hashed_password",
            role=UserRole.CITIZEN,
            is_verified=True,
            is_active=True,
            deleted_at=datetime.now(timezone.utc),
        )
        db_session.add(user)
        await db_session.commit()

        # Try to get the deleted user
        response = await client.get(
            f"/api/v1/users/{user_id}",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert response.status_code == 404
