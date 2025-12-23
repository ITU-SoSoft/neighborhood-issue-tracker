"""Unit tests for NotificationService."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.notification import NotificationType
from app.models.ticket import Ticket, TicketFollower, TicketStatus
from app.models.user import User, UserRole
from app.services.notification_service import (
    create_notification,
    notify_ticket_created,
    notify_ticket_followed,
    notify_ticket_status_changed,
)


class TestCreateNotification:
    """Tests for create_notification function."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        return db

    async def test_creates_notification_with_all_fields(self, mock_db):
        """Should create notification with all provided fields."""
        user_id = uuid.uuid4()
        ticket_id = uuid.uuid4()

        await create_notification(
            db=mock_db,
            user_id=user_id,
            notification_type=NotificationType.TICKET_CREATED,
            title="Test Notification",
            message="This is a test message",
            ticket_id=ticket_id,
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

        # Verify the notification object passed to db.add
        notification = mock_db.add.call_args[0][0]
        assert notification.user_id == user_id
        assert notification.ticket_id == ticket_id
        assert notification.notification_type == NotificationType.TICKET_CREATED
        assert notification.title == "Test Notification"
        assert notification.message == "This is a test message"
        assert notification.is_read is False

    async def test_creates_notification_without_ticket_id(self, mock_db):
        """Should create notification without ticket_id (optional field)."""
        user_id = uuid.uuid4()

        await create_notification(
            db=mock_db,
            user_id=user_id,
            notification_type=NotificationType.TICKET_CREATED,
            title="General Notification",
            message="No ticket associated",
            ticket_id=None,
        )

        notification = mock_db.add.call_args[0][0]
        assert notification.ticket_id is None


class TestNotifyTicketCreated:
    """Tests for notify_ticket_created function."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        return db

    @pytest.fixture
    def ticket(self):
        """Create a test ticket."""
        return Ticket(
            id=uuid.uuid4(),
            title="Pothole on Main Street",
            description="Large pothole needs repair",
            status=TicketStatus.NEW,
            reporter_id=uuid.uuid4(),
            category_id=uuid.uuid4(),
            location_id=uuid.uuid4(),
        )

    async def test_notifies_reporter(self, mock_db, ticket):
        """Should create notification for the ticket reporter."""
        await notify_ticket_created(mock_db, ticket)

        mock_db.add.assert_called_once()
        notification = mock_db.add.call_args[0][0]
        assert notification.user_id == ticket.reporter_id
        assert notification.ticket_id == ticket.id
        assert notification.notification_type == NotificationType.TICKET_CREATED
        assert "Pothole on Main Street" in notification.message
        assert notification.title == "Ticket Created"


class TestNotifyTicketFollowed:
    """Tests for notify_ticket_followed function."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        return db

    @pytest.fixture
    def ticket(self):
        """Create a test ticket with a reporter."""
        return Ticket(
            id=uuid.uuid4(),
            title="Street Light Broken",
            description="Light not working",
            status=TicketStatus.NEW,
            reporter_id=uuid.uuid4(),
            category_id=uuid.uuid4(),
            location_id=uuid.uuid4(),
        )

    @pytest.fixture
    def other_user(self):
        """Create another user who follows the ticket."""
        return User(
            id=uuid.uuid4(),
            phone_number="+905557778899",
            name="Follower User",
            role=UserRole.CITIZEN,
        )

    async def test_notifies_reporter_when_others_follow(
        self, mock_db, ticket, other_user
    ):
        """Should notify reporter when another user follows their ticket."""
        await notify_ticket_followed(mock_db, ticket, other_user)

        mock_db.add.assert_called_once()
        notification = mock_db.add.call_args[0][0]
        assert notification.user_id == ticket.reporter_id
        assert notification.notification_type == NotificationType.TICKET_FOLLOWED
        assert "Follower User" in notification.message
        assert "Street Light Broken" in notification.message

    async def test_does_not_notify_when_reporter_follows_own_ticket(
        self, mock_db, ticket
    ):
        """Should NOT notify when user follows their own ticket."""
        # Create a follower who is the reporter
        reporter_as_follower = User(
            id=ticket.reporter_id,  # Same as reporter
            phone_number="+905551234567",
            name="Reporter",
            role=UserRole.CITIZEN,
        )

        await notify_ticket_followed(mock_db, ticket, reporter_as_follower)

        # Should not add any notification
        mock_db.add.assert_not_called()


class TestNotifyTicketStatusChanged:
    """Tests for notify_ticket_status_changed function."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def ticket(self):
        """Create a test ticket."""
        return Ticket(
            id=uuid.uuid4(),
            title="Trash Collection Issue",
            description="Trash not collected",
            status=TicketStatus.IN_PROGRESS,
            reporter_id=uuid.uuid4(),
            category_id=uuid.uuid4(),
            location_id=uuid.uuid4(),
        )

    @pytest.fixture
    def support_user(self):
        """Create a support user who changes status."""
        return User(
            id=uuid.uuid4(),
            phone_number="+905559876543",
            name="Support Agent",
            role=UserRole.SUPPORT,
        )

    async def test_notifies_reporter_on_status_change(
        self, mock_db, ticket, support_user
    ):
        """Should notify reporter when status changes (if not changed by reporter)."""
        # Mock follower query to return empty list
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        await notify_ticket_status_changed(
            db=mock_db,
            ticket=ticket,
            old_status=TicketStatus.NEW,
            new_status=TicketStatus.IN_PROGRESS,
            changed_by=support_user,
        )

        mock_db.add.assert_called_once()
        notification = mock_db.add.call_args[0][0]
        assert notification.user_id == ticket.reporter_id
        assert notification.notification_type == NotificationType.TICKET_STATUS_CHANGED
        assert "New" in notification.message and "In Progress" in notification.message

    async def test_does_not_notify_reporter_if_self_change(self, mock_db, ticket):
        """Should NOT notify reporter if they changed the status themselves."""
        # Reporter changes their own ticket status
        reporter_user = User(
            id=ticket.reporter_id,
            phone_number="+905551234567",
            name="Reporter",
            role=UserRole.CITIZEN,
        )

        # Mock follower query
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        await notify_ticket_status_changed(
            db=mock_db,
            ticket=ticket,
            old_status=TicketStatus.NEW,
            new_status=TicketStatus.IN_PROGRESS,
            changed_by=reporter_user,
        )

        # Should not create notification for reporter
        mock_db.add.assert_not_called()

    async def test_notifies_followers_on_status_change(
        self, mock_db, ticket, support_user
    ):
        """Should notify followers (except reporter and changer) on status change."""
        follower_id = uuid.uuid4()
        follower = TicketFollower(
            ticket_id=ticket.id,
            user_id=follower_id,
        )

        # Mock follower query
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [follower]
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        await notify_ticket_status_changed(
            db=mock_db,
            ticket=ticket,
            old_status=TicketStatus.NEW,
            new_status=TicketStatus.IN_PROGRESS,
            changed_by=support_user,
        )

        # Should create 2 notifications: one for reporter, one for follower
        assert mock_db.add.call_count == 2

    async def test_status_labels_in_message(self, mock_db, ticket, support_user):
        """Should use human-readable status labels in notification message."""
        # Mock follower query
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        await notify_ticket_status_changed(
            db=mock_db,
            ticket=ticket,
            old_status=TicketStatus.IN_PROGRESS,
            new_status=TicketStatus.RESOLVED,
            changed_by=support_user,
        )

        notification = mock_db.add.call_args[0][0]
        # Should use "In Progress" and "Resolved" not "IN_PROGRESS" and "RESOLVED"
        assert "In Progress" in notification.message
        assert "Resolved" in notification.message
