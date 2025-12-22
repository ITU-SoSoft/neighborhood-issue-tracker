"""Tests for escalation API endpoints."""

import pytest
from httpx import AsyncClient

from tests.conftest import auth_headers


# ============================================================================
# POST /api/v1/escalations - Create escalation
# ============================================================================


@pytest.mark.asyncio
async def test_support_creates_escalation_for_own_team_ticket(
    client: AsyncClient,
    ticket,
    support_with_team_token: str,
):
    """Support user can create escalation for their team's ticket."""
    response = await client.post(
        "/api/v1/escalations",
        json={"ticket_id": str(ticket.id), "reason": "Need manager approval for this issue"},
        headers=auth_headers(support_with_team_token),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["ticket_id"] == str(ticket.id)
    assert data["reason"] == "Need manager approval for this issue"
    assert data["status"] == "PENDING"


@pytest.mark.asyncio
async def test_support_cannot_escalate_another_teams_ticket(
    client: AsyncClient,
    ticket,
    support_other_team_token: str,
):
    """Support user cannot escalate a ticket assigned to another team."""
    response = await client.post(
        "/api/v1/escalations",
        json={"ticket_id": str(ticket.id), "reason": "Trying to escalate another team's ticket"},
        headers=auth_headers(support_other_team_token),
    )
    assert response.status_code == 403
    assert "your team" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_support_cannot_escalate_unassigned_ticket(
    client: AsyncClient,
    unassigned_ticket,
    support_with_team_token: str,
):
    """Support user cannot escalate an unassigned ticket."""
    response = await client.post(
        "/api/v1/escalations",
        json={"ticket_id": str(unassigned_ticket.id), "reason": "Trying to escalate unassigned ticket"},
        headers=auth_headers(support_with_team_token),
    )
    assert response.status_code == 403
    assert "unassigned" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_citizen_cannot_create_escalation(
    client: AsyncClient,
    ticket,
    citizen_token: str,
):
    """Citizen users cannot create escalations."""
    response = await client.post(
        "/api/v1/escalations",
        json={"ticket_id": str(ticket.id), "reason": "Citizen trying to escalate"},
        headers=auth_headers(citizen_token),
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_escalation_ticket_not_found(
    client: AsyncClient,
    support_with_team_token: str,
):
    """Creating escalation for non-existent ticket returns 404."""
    import uuid
    response = await client.post(
        "/api/v1/escalations",
        json={"ticket_id": str(uuid.uuid4()), "reason": "Non-existent ticket"},
        headers=auth_headers(support_with_team_token),
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cannot_escalate_with_pending_escalation(
    client: AsyncClient,
    escalation,
    support_with_team_token: str,
):
    """Cannot create escalation if a PENDING one already exists for the ticket."""
    response = await client.post(
        "/api/v1/escalations",
        json={"ticket_id": str(escalation.ticket_id), "reason": "Duplicate escalation"},
        headers=auth_headers(support_with_team_token),
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_can_reescalate_after_rejection(
    client: AsyncClient,
    rejected_escalation,
    support_with_team_token: str,
):
    """Can create a new escalation after the previous one was rejected."""
    response = await client.post(
        "/api/v1/escalations",
        json={"ticket_id": str(rejected_escalation.ticket_id), "reason": "Re-escalating after rejection"},
        headers=auth_headers(support_with_team_token),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "PENDING"
    assert data["reason"] == "Re-escalating after rejection"


@pytest.mark.asyncio
async def test_cannot_reescalate_after_approval(
    client: AsyncClient,
    approved_escalation,
    support_with_team_token: str,
):
    """Cannot create a new escalation after the previous one was approved."""
    response = await client.post(
        "/api/v1/escalations",
        json={"ticket_id": str(approved_escalation.ticket_id), "reason": "Trying to escalate after approval"},
        headers=auth_headers(support_with_team_token),
    )
    assert response.status_code == 403
    assert "already approved" in response.json()["detail"].lower()


# ============================================================================
# GET /api/v1/escalations - List escalations
# ============================================================================


@pytest.mark.asyncio
async def test_manager_sees_all_escalations(
    client: AsyncClient,
    escalation,
    manager_token: str,
):
    """Manager can see all escalations."""
    response = await client.get(
        "/api/v1/escalations",
        headers=auth_headers(manager_token),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1


@pytest.mark.asyncio
async def test_support_sees_only_own_team_escalations(
    client: AsyncClient,
    escalation,
    support_with_team_token: str,
):
    """Support user sees only their team's escalations."""
    response = await client.get(
        "/api/v1/escalations",
        headers=auth_headers(support_with_team_token),
    )
    assert response.status_code == 200
    data = response.json()
    # The escalation fixture belongs to the same team as support_user_with_team
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_support_other_team_sees_no_escalations(
    client: AsyncClient,
    escalation,
    support_other_team_token: str,
):
    """Support user from another team sees no escalations for first team's tickets."""
    response = await client.get(
        "/api/v1/escalations",
        headers=auth_headers(support_other_team_token),
    )
    assert response.status_code == 200
    data = response.json()
    # The escalation belongs to a different team
    assert data["total"] == 0
    assert len(data["items"]) == 0


@pytest.mark.asyncio
async def test_citizen_cannot_list_escalations(
    client: AsyncClient,
    citizen_token: str,
):
    """Citizen users cannot list escalations."""
    response = await client.get(
        "/api/v1/escalations",
        headers=auth_headers(citizen_token),
    )
    assert response.status_code == 403


# ============================================================================
# GET /api/v1/escalations/{id} - Get single escalation
# ============================================================================


@pytest.mark.asyncio
async def test_support_can_view_escalation(
    client: AsyncClient,
    escalation,
    support_with_team_token: str,
):
    """Support user can view an escalation."""
    response = await client.get(
        f"/api/v1/escalations/{escalation.id}",
        headers=auth_headers(support_with_team_token),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(escalation.id)


@pytest.mark.asyncio
async def test_escalation_not_found(
    client: AsyncClient,
    support_with_team_token: str,
):
    """Getting non-existent escalation returns 404."""
    import uuid
    response = await client.get(
        f"/api/v1/escalations/{uuid.uuid4()}",
        headers=auth_headers(support_with_team_token),
    )
    assert response.status_code == 404


# ============================================================================
# PATCH /api/v1/escalations/{id}/approve - Approve escalation
# ============================================================================


@pytest.mark.asyncio
async def test_manager_approves_escalation(
    client: AsyncClient,
    escalation,
    manager_token: str,
):
    """Manager can approve an escalation."""
    response = await client.patch(
        f"/api/v1/escalations/{escalation.id}/approve",
        json={"comment": "Approved by manager"},
        headers=auth_headers(manager_token),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "APPROVED"
    assert data["review_comment"] == "Approved by manager"


@pytest.mark.asyncio
async def test_support_cannot_approve_escalation(
    client: AsyncClient,
    escalation,
    support_with_team_token: str,
):
    """Support users cannot approve escalations."""
    response = await client.patch(
        f"/api/v1/escalations/{escalation.id}/approve",
        json={"comment": "Support trying to approve"},
        headers=auth_headers(support_with_team_token),
    )
    assert response.status_code == 403


# ============================================================================
# PATCH /api/v1/escalations/{id}/reject - Reject escalation
# ============================================================================


@pytest.mark.asyncio
async def test_manager_rejects_escalation(
    client: AsyncClient,
    escalation,
    manager_token: str,
):
    """Manager can reject an escalation."""
    response = await client.patch(
        f"/api/v1/escalations/{escalation.id}/reject",
        json={"comment": "Not a valid escalation reason"},
        headers=auth_headers(manager_token),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "REJECTED"
    assert data["review_comment"] == "Not a valid escalation reason"


@pytest.mark.asyncio
async def test_support_cannot_reject_escalation(
    client: AsyncClient,
    escalation,
    support_with_team_token: str,
):
    """Support users cannot reject escalations."""
    response = await client.patch(
        f"/api/v1/escalations/{escalation.id}/reject",
        json={"comment": "Support trying to reject"},
        headers=auth_headers(support_with_team_token),
    )
    assert response.status_code == 403
