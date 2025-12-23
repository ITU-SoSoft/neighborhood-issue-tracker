"""Integration tests for Notifications API endpoints."""

import uuid

from httpx import AsyncClient

from tests.conftest import auth_headers


# ============================================================================
# GET /api/v1/notifications - List notifications
# ============================================================================


class TestListNotifications:
    """Tests for GET /api/v1/notifications."""

    async def test_user_lists_own_notifications(
        self, client: AsyncClient, citizen_token: str, db_session, citizen_user
    ):
        """User should see their own notifications."""
        from app.models.notification import Notification, NotificationType

        # Create a notification for the user
        notification = Notification(
            id=uuid.uuid4(),
            user_id=citizen_user.id,
            notification_type=NotificationType.TICKET_CREATED,
            title="Test Notification",
            message="This is a test notification.",
            is_read=False,
        )
        db_session.add(notification)
        await db_session.commit()

        response = await client.get(
            "/api/v1/notifications",
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 1

    async def test_unauthenticated_cannot_list_notifications(self, client: AsyncClient):
        """Unauthenticated requests should be rejected."""
        response = await client.get("/api/v1/notifications")
        assert response.status_code == 401


# ============================================================================
# GET /api/v1/notifications/unread-count - Get unread count
# ============================================================================


class TestUnreadCount:
    """Tests for GET /api/v1/notifications/unread-count."""

    async def test_get_unread_count(
        self, client: AsyncClient, citizen_token: str, db_session, citizen_user
    ):
        """Should return the count of unread notifications."""
        from app.models.notification import Notification, NotificationType

        # Create unread notifications
        for i in range(3):
            notification = Notification(
                id=uuid.uuid4(),
                user_id=citizen_user.id,
                notification_type=NotificationType.TICKET_CREATED,
                title=f"Notification {i}",
                message=f"Message {i}",
                is_read=False,
            )
            db_session.add(notification)
        await db_session.commit()

        response = await client.get(
            "/api/v1/notifications/unread-count",
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert data["count"] >= 3


# ============================================================================
# PATCH /api/v1/notifications/{id}/read - Mark as read
# ============================================================================


class TestMarkAsRead:
    """Tests for PATCH /api/v1/notifications/{id}/read."""

    async def test_mark_notification_as_read(
        self, client: AsyncClient, citizen_token: str, db_session, citizen_user
    ):
        """Should mark a notification as read."""
        from app.models.notification import Notification, NotificationType

        notification = Notification(
            id=uuid.uuid4(),
            user_id=citizen_user.id,
            notification_type=NotificationType.TICKET_CREATED,
            title="Unread Notification",
            message="This will be marked as read.",
            is_read=False,
        )
        db_session.add(notification)
        await db_session.commit()

        response = await client.patch(
            f"/api/v1/notifications/{notification.id}/read",
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_read"] is True

    async def test_cannot_mark_others_notification(
        self, client: AsyncClient, citizen_token: str, db_session, support_user
    ):
        """Should not be able to mark another user's notification as read."""
        from app.models.notification import Notification, NotificationType

        # Use an existing user (support_user) to create the notification
        notification = Notification(
            id=uuid.uuid4(),
            user_id=support_user.id,  # Use existing user
            notification_type=NotificationType.TICKET_CREATED,
            title="Other User Notification",
            message="This belongs to someone else.",
            is_read=False,
        )
        db_session.add(notification)
        await db_session.commit()

        response = await client.patch(
            f"/api/v1/notifications/{notification.id}/read",
            headers=auth_headers(citizen_token),
        )
        assert response.status_code in [403, 404]

    async def test_nonexistent_notification_returns_404(
        self, client: AsyncClient, citizen_token: str
    ):
        """Should return 404 for nonexistent notification."""
        response = await client.patch(
            f"/api/v1/notifications/{uuid.uuid4()}/read",
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 404


# ============================================================================
# PATCH /api/v1/notifications/read-all - Mark all as read
# ============================================================================


class TestMarkAllAsRead:
    """Tests for PATCH /api/v1/notifications/read-all."""

    async def test_mark_all_notifications_as_read(
        self, client: AsyncClient, citizen_token: str, db_session, citizen_user
    ):
        """Should mark all notifications as read."""
        from app.models.notification import Notification, NotificationType

        # Create multiple unread notifications
        for i in range(5):
            notification = Notification(
                id=uuid.uuid4(),
                user_id=citizen_user.id,
                notification_type=NotificationType.TICKET_CREATED,
                title=f"Notification {i}",
                message=f"Message {i}",
                is_read=False,
            )
            db_session.add(notification)
        await db_session.commit()

        response = await client.patch(
            "/api/v1/notifications/read-all",
            headers=auth_headers(citizen_token),
        )
        assert response.status_code == 200

        # Verify all are marked as read
        count_response = await client.get(
            "/api/v1/notifications/unread-count",
            headers=auth_headers(citizen_token),
        )
        assert count_response.status_code == 200
        assert count_response.json()["count"] == 0

    async def test_mark_all_read_with_no_notifications(
        self, client: AsyncClient, db_session, manager_token: str
    ):
        """Should succeed even with no notifications."""
        # Use manager_token which already has an existing user
        response = await client.patch(
            "/api/v1/notifications/read-all",
            headers=auth_headers(manager_token),
        )
        assert response.status_code == 200

    async def test_mark_all_read_requires_auth(self, client: AsyncClient):
        """Unauthenticated request to read-all should be rejected."""
        response = await client.patch("/api/v1/notifications/read-all")

        assert response.status_code == 401
