"""Integration tests for role-based permissions across the API."""

import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.escalation import EscalationRequest, EscalationStatus
from app.models.ticket import Ticket, TicketStatus
from app.models.user import User
from tests.conftest import auth_headers


# ============================================================================
# Test: Role-Based Access Control
# ============================================================================


class TestRoleBasedAccess:
    """Tests for role-based access control across endpoints."""

    async def test_citizen_cannot_access_analytics(
        self,
        client: AsyncClient,
        citizen_token: str,
    ):
        """Citizen should not be able to access analytics endpoints."""
        response = await client.get(
            "/api/v1/analytics/dashboard",
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 403

    async def test_support_can_access_analytics(
        self,
        client: AsyncClient,
        support_token: str,
    ):
        """Support user should be able to access analytics."""
        response = await client.get(
            "/api/v1/analytics/dashboard",
            headers=auth_headers(support_token),
        )
        assert response.status_code == 200

    async def test_manager_can_access_analytics(
        self,
        client: AsyncClient,
        manager_token: str,
    ):
        """Manager should be able to access analytics."""
        response = await client.get(
            "/api/v1/analytics/dashboard",
            headers=auth_headers(manager_token),
        )
        assert response.status_code == 200


class TestEscalationPermissions:
    """Tests for escalation-related permissions."""

    async def test_only_manager_can_approve_escalation(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        escalation: EscalationRequest,
        manager_token: str,
        support_token: str,
        citizen_token: str,
    ):
        """Only managers should be able to approve escalations."""
        # Support cannot approve
        response = await client.patch(
            f"/api/v1/escalations/{escalation.id}/approve",
            headers=auth_headers(support_token),
            json={"review_comment": "Approved"},
        )
        assert response.status_code == 403

        # Citizen cannot approve
        response = await client.patch(
            f"/api/v1/escalations/{escalation.id}/approve",
            headers=auth_headers(citizen_token),
            json={"review_comment": "Approved"},
        )
        assert response.status_code == 403

        # Manager can approve
        response = await client.patch(
            f"/api/v1/escalations/{escalation.id}/approve",
            headers=auth_headers(manager_token),
            json={"review_comment": "Approved by manager"},
        )
        assert response.status_code == 200

    async def test_only_manager_can_reject_escalation(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        ticket: Ticket,
        support_user_with_team: User,
        manager_token: str,
        support_token: str,
    ):
        """Only managers should be able to reject escalations."""
        # Create a fresh escalation for this test
        escalation = EscalationRequest(
            id=uuid.uuid4(),
            ticket_id=ticket.id,
            requester_id=support_user_with_team.id,
            reason="Test rejection permissions",
            status=EscalationStatus.PENDING,
        )
        db_session.add(escalation)
        ticket.status = TicketStatus.ESCALATED
        await db_session.commit()

        # Support cannot reject
        response = await client.patch(
            f"/api/v1/escalations/{escalation.id}/reject",
            headers=auth_headers(support_token),
            json={"review_comment": "Rejected"},
        )
        assert response.status_code == 403

        # Manager can reject
        response = await client.patch(
            f"/api/v1/escalations/{escalation.id}/reject",
            headers=auth_headers(manager_token),
            json={"review_comment": "Rejected by manager"},
        )
        assert response.status_code == 200


class TestTicketManagementPermissions:
    """Tests for ticket management permissions."""

    async def test_support_can_manage_team_tickets(
        self,
        client: AsyncClient,
        ticket: Ticket,
        support_with_team_token: str,
    ):
        """Support user can manage tickets assigned to their team."""
        # Support with team should be able to update status
        response = await client.patch(
            f"/api/v1/tickets/{ticket.id}/status",
            headers=auth_headers(support_with_team_token),
            json={"status": "IN_PROGRESS"},
        )
        assert response.status_code == 200

    async def test_support_can_manage_any_ticket(
        self,
        client: AsyncClient,
        ticket: Ticket,
        support_other_team_token: str,
    ):
        """Support user can manage any ticket (no team restriction currently implemented)."""
        response = await client.patch(
            f"/api/v1/tickets/{ticket.id}/status",
            headers=auth_headers(support_other_team_token),
            json={"status": "IN_PROGRESS"},
        )
        # Currently, support users can manage any ticket regardless of team assignment
        assert response.status_code == 200
    async def test_manager_can_manage_any_ticket(
        self,
        client: AsyncClient,
        ticket: Ticket,
        manager_token: str,
    ):
        """Manager can manage any ticket regardless of team."""
        response = await client.patch(
            f"/api/v1/tickets/{ticket.id}/status",
            headers=auth_headers(manager_token),
            json={"status": "IN_PROGRESS"},
        )
        assert response.status_code == 200


class TestUserManagementPermissions:
    """Tests for user management permissions."""

    async def test_only_manager_can_delete_users(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        citizen_token: str,
        support_token: str,
        manager_token: str,
    ):
        """Only managers should be able to delete users."""
        from app.models.user import User as UserModel, UserRole
        from app.core.security import hash_password

        # Create a user to delete
        user_id = uuid.uuid4()
        user = UserModel(
            id=user_id,
            phone_number="+905559998800",
            name="Delete Test User",
            email="delete_perm_test@test.com",
            password_hash=hash_password("password"),
            role=UserRole.CITIZEN,
            is_verified=True,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

        # Citizen cannot delete
        response = await client.delete(
            f"/api/v1/users/{user_id}",
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 403

        # Support cannot delete
        response = await client.delete(
            f"/api/v1/users/{user_id}",
            headers=auth_headers(support_token),
        )
        assert response.status_code == 403

        # Manager can delete
        response = await client.delete(
            f"/api/v1/users/{user_id}",
            headers=auth_headers(manager_token),
        )
        assert response.status_code == 204

    async def test_only_manager_can_change_user_roles(
        self,
        client: AsyncClient,
        citizen_user: User,
        citizen_token: str,
        support_token: str,
        manager_token: str,
    ):
        """Only managers should be able to change user roles."""
        # Citizen cannot change roles
        response = await client.patch(
            f"/api/v1/users/{citizen_user.id}/role",
            headers=auth_headers(citizen_token),
            json={"role": "SUPPORT"},
        )
        assert response.status_code == 403

        # Support cannot change roles
        response = await client.patch(
            f"/api/v1/users/{citizen_user.id}/role",
            headers=auth_headers(support_token),
            json={"role": "SUPPORT"},
        )
        assert response.status_code == 403

        # Manager can change roles
        response = await client.patch(
            f"/api/v1/users/{citizen_user.id}/role",
            headers=auth_headers(manager_token),
            json={"role": "SUPPORT"},
        )
        assert response.status_code == 200
