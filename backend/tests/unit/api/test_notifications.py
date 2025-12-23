"""Unit tests for notifications API endpoints."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.api.v1.notifications import (
    list_notifications,
    get_unread_count,
    mark_as_read,
    mark_all_as_read,
)
from app.models.notification import Notification, NotificationType
from app.models.user import User, UserRole


class TestListNotifications:
    """Tests for list_notifications endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def citizen_user(self):
        """Create a mock citizen user."""
        return User(
            id=uuid.uuid4(),
            phone_number="+905551234567",
            name="Test Citizen",
            role=UserRole.CITIZEN,
        )

    async def test_list_notifications_success(self, mock_db, citizen_user):
        """Should return paginated notifications."""
        now = datetime.now(timezone.utc)
        notification = Notification(
            id=uuid.uuid4(),
            user_id=citizen_user.id,
            notification_type=NotificationType.TICKET_STATUS_CHANGED,
            title="Status Updated",
            message="Your ticket status changed",
            is_read=False,
            created_at=now,
        )

        # Mock count
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        # Mock notifications
        mock_notifications_result = MagicMock()
        mock_unique = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [notification]
        mock_unique.scalars.return_value = mock_scalars
        mock_notifications_result.unique.return_value = mock_unique

        mock_db.execute.side_effect = [mock_count_result, mock_notifications_result]

        result = await list_notifications(
            citizen_user, mock_db, unread_only=False, page=1, page_size=20
        )

        assert result.total == 1
        assert len(result.items) == 1
        assert result.page == 1
        assert result.page_size == 20

    async def test_list_notifications_unread_only(self, mock_db, citizen_user):
        """Should filter to unread notifications only."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0

        mock_notifications_result = MagicMock()
        mock_unique = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_unique.scalars.return_value = mock_scalars
        mock_notifications_result.unique.return_value = mock_unique

        mock_db.execute.side_effect = [mock_count_result, mock_notifications_result]

        result = await list_notifications(
            citizen_user, mock_db, unread_only=True, page=1, page_size=20
        )

        assert result.total == 0
        assert len(result.items) == 0


class TestGetUnreadCount:
    """Tests for get_unread_count endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def citizen_user(self):
        """Create a mock citizen user."""
        return User(
            id=uuid.uuid4(),
            phone_number="+905551234567",
            name="Test Citizen",
            role=UserRole.CITIZEN,
        )

    async def test_get_unread_count_with_notifications(self, mock_db, citizen_user):
        """Should return count of unread notifications."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 5
        mock_db.execute.return_value = mock_result

        result = await get_unread_count(citizen_user, mock_db)

        assert result["count"] == 5

    async def test_get_unread_count_none(self, mock_db, citizen_user):
        """Should return 0 when no unread notifications."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 0
        mock_db.execute.return_value = mock_result

        result = await get_unread_count(citizen_user, mock_db)

        assert result["count"] == 0


class TestMarkAsRead:
    """Tests for mark_as_read endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        return db

    @pytest.fixture
    def citizen_user(self):
        """Create a mock citizen user."""
        return User(
            id=uuid.uuid4(),
            phone_number="+905551234567",
            name="Test Citizen",
            role=UserRole.CITIZEN,
        )

    async def test_mark_as_read_success(self, mock_db, citizen_user):
        """Should mark a notification as read."""
        notification_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        notification = Notification(
            id=notification_id,
            user_id=citizen_user.id,
            notification_type=NotificationType.TICKET_STATUS_CHANGED,
            title="Status Updated",
            message="Your ticket status changed",
            is_read=False,
            created_at=now,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = notification
        mock_db.execute.return_value = mock_result

        result = await mark_as_read(notification_id, citizen_user, mock_db)

        assert notification.is_read is True
        assert notification.read_at is not None
        mock_db.commit.assert_called_once()

    async def test_mark_as_read_not_found(self, mock_db, citizen_user):
        """Should raise HTTPException when notification not found."""
        notification_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await mark_as_read(notification_id, citizen_user, mock_db)

        assert exc_info.value.status_code == 404


class TestMarkAllAsRead:
    """Tests for mark_all_as_read endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        return db

    @pytest.fixture
    def citizen_user(self):
        """Create a mock citizen user."""
        return User(
            id=uuid.uuid4(),
            phone_number="+905551234567",
            name="Test Citizen",
            role=UserRole.CITIZEN,
        )

    async def test_mark_all_as_read_success(self, mock_db, citizen_user):
        """Should mark all notifications as read."""
        now = datetime.now(timezone.utc)
        notifications = [
            Notification(
                id=uuid.uuid4(),
                user_id=citizen_user.id,
                notification_type=NotificationType.TICKET_STATUS_CHANGED,
                title="Update 1",
                message="Message 1",
                is_read=False,
                created_at=now,
            ),
            Notification(
                id=uuid.uuid4(),
                user_id=citizen_user.id,
                notification_type=NotificationType.COMMENT_ADDED,
                title="Update 2",
                message="Message 2",
                is_read=False,
                created_at=now,
            ),
        ]

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = notifications
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        result = await mark_all_as_read(citizen_user, mock_db)

        assert result["message"] == "All notifications marked as read"
        for notification in notifications:
            assert notification.is_read is True
            assert notification.read_at is not None
        mock_db.commit.assert_called_once()

    async def test_mark_all_as_read_no_notifications(self, mock_db, citizen_user):
        """Should succeed even with no unread notifications."""
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        result = await mark_all_as_read(citizen_user, mock_db)

        assert result["message"] == "All notifications marked as read"
        mock_db.commit.assert_called_once()
