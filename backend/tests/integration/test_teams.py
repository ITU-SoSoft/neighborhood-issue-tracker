"""Integration tests for Teams API endpoints."""

import uuid

from httpx import AsyncClient

from tests.conftest import auth_headers


# ============================================================================
# GET /api/v1/teams - List teams
# ============================================================================


class TestListTeams:
    """Tests for GET /api/v1/teams."""

    async def test_support_lists_teams(
        self, client: AsyncClient, support_token: str, team
    ):
        """Support user should not be able to list teams (manager only)."""
        response = await client.get(
            "/api/v1/teams",
            headers=auth_headers(support_token),
        )
        # Only managers can list teams
        assert response.status_code == 403

    async def test_manager_lists_teams(
        self, client: AsyncClient, manager_token: str, team
    ):
        """Manager should be able to list teams."""
        response = await client.get(
            "/api/v1/teams",
            headers=auth_headers(manager_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    async def test_citizen_cannot_list_teams(
        self, client: AsyncClient, citizen_token: str
    ):
        """Citizen should not be able to list teams."""
        response = await client.get(
            "/api/v1/teams",
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 403


# ============================================================================
# GET /api/v1/teams/{id} - Get single team
# ============================================================================


class TestGetTeam:
    """Tests for GET /api/v1/teams/{id}."""

    async def test_support_gets_team(
        self, client: AsyncClient, support_token: str, team
    ):
        """Support user should not be able to get team details (manager only)."""
        response = await client.get(
            f"/api/v1/teams/{team.id}",
            headers=auth_headers(support_token),
        )
        # Only managers can view team details
        assert response.status_code == 403

    async def test_manager_gets_team(
        self, client: AsyncClient, manager_token: str, team
    ):
        """Manager should be able to get team details."""
        response = await client.get(
            f"/api/v1/teams/{team.id}",
            headers=auth_headers(manager_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(team.id)
        assert data["name"] == team.name

    async def test_nonexistent_team_returns_404(
        self, client: AsyncClient, manager_token: str
    ):
        """Should return 404 for nonexistent team."""
        response = await client.get(
            f"/api/v1/teams/{uuid.uuid4()}",
            headers=auth_headers(manager_token),
        )
        assert response.status_code == 404


# ============================================================================
# POST /api/v1/teams - Create team
# ============================================================================


class TestCreateTeam:
    """Tests for POST /api/v1/teams."""

    async def test_manager_creates_team(self, client: AsyncClient, manager_token: str):
        """Manager should be able to create a team."""
        response = await client.post(
            "/api/v1/teams",
            json={
                "name": "New Test Team",
                "description": "A new team for testing purposes",
            },
            headers=auth_headers(manager_token),
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Test Team"
        assert data["description"] == "A new team for testing purposes"

    async def test_support_cannot_create_team(
        self, client: AsyncClient, support_token: str
    ):
        """Support user should not be able to create teams."""
        response = await client.post(
            "/api/v1/teams",
            json={"name": "Attempted Team", "description": "Should fail"},
            headers=auth_headers(support_token),
        )
        assert response.status_code == 403

    async def test_citizen_cannot_create_team(
        self, client: AsyncClient, citizen_token: str
    ):
        """Citizen should not be able to create teams."""
        response = await client.post(
            "/api/v1/teams",
            json={"name": "Citizen Team", "description": "Should fail"},
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 403

    async def test_team_name_required(self, client: AsyncClient, manager_token: str):
        """Team name should be required."""
        response = await client.post(
            "/api/v1/teams",
            json={"description": "No name provided"},
            headers=auth_headers(manager_token),
        )
        assert response.status_code == 422


# ============================================================================
# PUT /api/v1/teams/{id} - Update team
# ============================================================================


class TestUpdateTeam:
    """Tests for PUT /api/v1/teams/{id}."""

    async def test_manager_updates_team(
        self, client: AsyncClient, manager_token: str, team
    ):
        """Manager should be able to update a team."""
        response = await client.put(
            f"/api/v1/teams/{team.id}",
            json={
                "name": "Updated Team Name",
                "description": "Updated description",
            },
            headers=auth_headers(manager_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Team Name"

    async def test_support_cannot_update_team(
        self, client: AsyncClient, support_token: str, team
    ):
        """Support user should not be able to update teams."""
        response = await client.put(
            f"/api/v1/teams/{team.id}",
            json={"name": "Should Not Work"},
            headers=auth_headers(support_token),
        )
        assert response.status_code == 403


# ============================================================================
# DELETE /api/v1/teams/{id} - Delete team
# ============================================================================


class TestDeleteTeam:
    """Tests for DELETE /api/v1/teams/{id}."""

    async def test_manager_deletes_team(
        self, client: AsyncClient, manager_token: str, db_session
    ):
        """Manager should be able to delete a team."""
        from app.models.team import Team

        # Create a team to delete
        team_to_delete = Team(
            id=uuid.uuid4(),
            name="Team To Delete",
            description="This team will be deleted",
        )
        db_session.add(team_to_delete)
        await db_session.commit()

        response = await client.delete(
            f"/api/v1/teams/{team_to_delete.id}",
            headers=auth_headers(manager_token),
        )
        assert response.status_code == 204

    async def test_support_cannot_delete_team(
        self, client: AsyncClient, support_token: str, team
    ):
        """Support user should not be able to delete teams."""
        response = await client.delete(
            f"/api/v1/teams/{team.id}",
            headers=auth_headers(support_token),
        )
        assert response.status_code == 403


# ============================================================================
# POST /api/v1/teams/{id}/members/{user_id} - Add member to team
# ============================================================================


class TestTeamMembers:
    """Tests for team member management."""

    async def test_manager_adds_member_to_team(
        self, client: AsyncClient, manager_token: str, db_session
    ):
        """Manager should be able to add members to a team."""
        from app.models.team import Team
        from app.models.user import User, UserRole

        # Create a fresh team and user for this test
        test_team = Team(
            id=uuid.uuid4(),
            name="Test Add Member Team",
            description="Team for testing add member",
        )
        db_session.add(test_team)

        new_support = User(
            id=uuid.uuid4(),
            phone_number="+905559998877",
            email="new_support_user@test.com",
            password_hash="dummy_hash",
            name="New Support User",
            role=UserRole.SUPPORT,
            is_verified=True,
            is_active=True,
        )
        db_session.add(new_support)
        await db_session.commit()

        response = await client.post(
            f"/api/v1/teams/{test_team.id}/members/{new_support.id}",
            headers=auth_headers(manager_token),
        )
        assert response.status_code in [200, 201]

    async def test_support_cannot_add_members(
        self, client: AsyncClient, support_token: str, team, citizen_user
    ):
        """Support user should not be able to add members to teams."""
        response = await client.post(
            f"/api/v1/teams/{team.id}/members/{citizen_user.id}",
            headers=auth_headers(support_token),
        )
        assert response.status_code == 403

    async def test_add_nonexistent_user_fails(
        self, client: AsyncClient, manager_token: str, team
    ):
        """Should fail when adding nonexistent user to team."""
        response = await client.post(
            f"/api/v1/teams/{team.id}/members/{uuid.uuid4()}",
            headers=auth_headers(manager_token),
        )
        assert response.status_code == 404

    async def test_manager_removes_member_from_team(
        self, client: AsyncClient, manager_token: str, support_user_with_team, team
    ):
        """Manager should be able to remove members from a team."""
        response = await client.delete(
            f"/api/v1/teams/{team.id}/members/{support_user_with_team.id}",
            headers=auth_headers(manager_token),
        )
        assert response.status_code in [200, 204]
