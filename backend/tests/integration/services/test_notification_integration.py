"""Integration tests for NotificationService - tests notification creation with real database."""

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.notification import Notification, NotificationType
from app.models.ticket import Location, Ticket, TicketFollower, TicketStatus
from app.models.user import User
from app.services.notification_service import (
    create_notification,
    notify_ticket_created,
    notify_ticket_followed,
    notify_ticket_status_changed,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
async def ticket_with_followers(
    db_session: AsyncSession,
    category: Category,
    citizen_user: User,
    support_user: User,
    manager_user: User,
) -> Ticket:
    """Create a ticket with multiple followers."""
    location = Location(
        id=uuid.uuid4(),
        latitude=41.0082,
        longitude=28.9784,
        coordinates="SRID=4326;POINT(28.9784 41.0082)",
        address="Test Address",
        district="Beyoglu",
        city="Istanbul",
    )
    db_session.add(location)
    await db_session.flush()

    ticket = Ticket(
        id=uuid.uuid4(),
        title="Ticket with Followers",
        description="A ticket that multiple people follow",
        status=TicketStatus.NEW,
        category_id=category.id,
        location_id=location.id,
        reporter_id=citizen_user.id,
    )
    db_session.add(ticket)
    await db_session.flush()

    # Add followers (reporter + 2 others)
    for user in [citizen_user, support_user, manager_user]:
        follower = TicketFollower(
            ticket_id=ticket.id,
            user_id=user.id,
        )
        db_session.add(follower)

    await db_session.commit()
    await db_session.refresh(ticket)
    return ticket


# ============================================================================
# Test: Create Notification
# ============================================================================


class TestCreateNotification:
    """Tests for create_notification function."""

    async def test_create_notification_basic(
        self,
        db_session: AsyncSession,
        citizen_user: User,
    ):
        """Should create a notification for a user."""
        notification = await create_notification(
            db=db_session,
            user_id=citizen_user.id,
            notification_type=NotificationType.TICKET_CREATED,
            title="Test Notification",
            message="This is a test notification message.",
        )

        assert notification is not None
        assert notification.user_id == citizen_user.id
        assert notification.title == "Test Notification"
        assert notification.message == "This is a test notification message."
        assert notification.is_read is False

    async def test_create_notification_with_ticket_reference(
        self,
        db_session: AsyncSession,
        citizen_user: User,
        ticket: Ticket,
    ):
        """Should create a notification linked to a ticket."""
        notification = await create_notification(
            db=db_session,
            user_id=citizen_user.id,
            notification_type=NotificationType.TICKET_STATUS_CHANGED,
            title="Status Changed",
            message="Your ticket status has changed.",
            ticket_id=ticket.id,
        )

        assert notification.ticket_id == ticket.id


# ============================================================================
# Test: Notify Ticket Created
# ============================================================================


class TestNotifyTicketCreated:
    """Tests for notify_ticket_created function."""

    async def test_notify_ticket_created(
        self,
        db_session: AsyncSession,
        ticket: Ticket,
        citizen_user: User,
    ):
        """Should notify reporter when their ticket is created."""
        # Ensure reporter is set
        ticket.reporter_id = citizen_user.id
        await db_session.commit()

        await notify_ticket_created(db_session, ticket)

        # Check notification was created
        result = await db_session.execute(
            select(Notification).where(
                Notification.user_id == citizen_user.id,
                Notification.ticket_id == ticket.id,
                Notification.notification_type == NotificationType.TICKET_CREATED,
            )
        )
        notification = result.scalar_one_or_none()

        assert notification is not None
        assert "Ticket Created" in notification.title
        assert ticket.title in notification.message


# ============================================================================
# Test: Notify Ticket Followed
# ============================================================================


class TestNotifyTicketFollowed:
    """Tests for notify_ticket_followed function."""

    async def test_notify_reporter_when_someone_follows(
        self,
        db_session: AsyncSession,
        ticket: Ticket,
        citizen_user: User,
        support_user: User,
    ):
        """Should notify reporter when someone else follows their ticket."""
        ticket.reporter_id = citizen_user.id
        await db_session.commit()

        await notify_ticket_followed(db_session, ticket, support_user)

        # Check notification was created for reporter
        result = await db_session.execute(
            select(Notification).where(
                Notification.user_id == citizen_user.id,
                Notification.ticket_id == ticket.id,
                Notification.notification_type == NotificationType.TICKET_FOLLOWED,
            )
        )
        notification = result.scalar_one_or_none()

        assert notification is not None
        assert "New Follower" in notification.title
        assert support_user.name in notification.message

    async def test_no_notification_when_reporter_follows_own_ticket(
        self,
        db_session: AsyncSession,
        ticket: Ticket,
        citizen_user: User,
    ):
        """Should NOT notify reporter when they follow their own ticket."""
        ticket.reporter_id = citizen_user.id
        await db_session.commit()

        await notify_ticket_followed(db_session, ticket, citizen_user)

        # Should NOT create a notification
        result = await db_session.execute(
            select(Notification).where(
                Notification.user_id == citizen_user.id,
                Notification.notification_type == NotificationType.TICKET_FOLLOWED,
            )
        )
        notification = result.scalar_one_or_none()

        assert notification is None


# ============================================================================
# Test: Notify Ticket Status Changed
# ============================================================================


class TestNotifyTicketStatusChanged:
    """Tests for notify_ticket_status_changed function."""

    async def test_notify_reporter_on_status_change(
        self,
        db_session: AsyncSession,
        ticket: Ticket,
        citizen_user: User,
        support_user: User,
    ):
        """Should notify reporter when status is changed by someone else."""
        ticket.reporter_id = citizen_user.id
        await db_session.commit()

        await notify_ticket_status_changed(
            db=db_session,
            ticket=ticket,
            old_status=TicketStatus.NEW,
            new_status=TicketStatus.IN_PROGRESS,
            changed_by=support_user,
        )

        # Check notification was created for reporter
        result = await db_session.execute(
            select(Notification).where(
                Notification.user_id == citizen_user.id,
                Notification.ticket_id == ticket.id,
                Notification.notification_type == NotificationType.TICKET_STATUS_CHANGED,
            )
        )
        notification = result.scalar_one_or_none()

        assert notification is not None
        assert "Status Updated" in notification.title
        assert "In Progress" in notification.message

    async def test_no_notification_when_reporter_changes_own_ticket(
        self,
        db_session: AsyncSession,
        ticket: Ticket,
        citizen_user: User,
    ):
        """Should NOT notify reporter when they change their own ticket status."""
        ticket.reporter_id = citizen_user.id
        await db_session.commit()

        await notify_ticket_status_changed(
            db=db_session,
            ticket=ticket,
            old_status=TicketStatus.NEW,
            new_status=TicketStatus.IN_PROGRESS,
            changed_by=citizen_user,  # Same as reporter
        )

        # Should NOT create a notification for reporter
        result = await db_session.execute(
            select(Notification).where(
                Notification.user_id == citizen_user.id,
                Notification.notification_type == NotificationType.TICKET_STATUS_CHANGED,
            )
        )
        notification = result.scalar_one_or_none()

        assert notification is None

    async def test_notify_all_followers_on_status_change(
        self,
        db_session: AsyncSession,
        ticket_with_followers: Ticket,
        citizen_user: User,
        support_user: User,
        manager_user: User,
    ):
        """Should notify all followers (except reporter and changer) on status change."""
        # Manager changes the status
        await notify_ticket_status_changed(
            db=db_session,
            ticket=ticket_with_followers,
            old_status=TicketStatus.NEW,
            new_status=TicketStatus.IN_PROGRESS,
            changed_by=manager_user,
        )

        # Reporter (citizen_user) should get "Status Updated" notification
        result = await db_session.execute(
            select(Notification).where(
                Notification.user_id == citizen_user.id,
                Notification.notification_type == NotificationType.TICKET_STATUS_CHANGED,
            )
        )
        reporter_notification = result.scalar_one_or_none()
        assert reporter_notification is not None
        assert "Status Updated" in reporter_notification.title

        # Support user (follower, not reporter, not changer) should get notification
        result = await db_session.execute(
            select(Notification).where(
                Notification.user_id == support_user.id,
                Notification.notification_type == NotificationType.TICKET_STATUS_CHANGED,
            )
        )
        follower_notification = result.scalar_one_or_none()
        assert follower_notification is not None
        assert "Ticket Updated" in follower_notification.title

        # Manager (changer) should NOT get notification
        result = await db_session.execute(
            select(Notification).where(
                Notification.user_id == manager_user.id,
                Notification.notification_type == NotificationType.TICKET_STATUS_CHANGED,
            )
        )
        changer_notification = result.scalar_one_or_none()
        assert changer_notification is None

    async def test_notification_content_contains_status_labels(
        self,
        db_session: AsyncSession,
        ticket: Ticket,
        citizen_user: User,
        support_user: User,
    ):
        """Should include human-readable status labels in notification message."""
        ticket.reporter_id = citizen_user.id
        await db_session.commit()

        await notify_ticket_status_changed(
            db=db_session,
            ticket=ticket,
            old_status=TicketStatus.IN_PROGRESS,
            new_status=TicketStatus.RESOLVED,
            changed_by=support_user,
        )

        result = await db_session.execute(
            select(Notification).where(
                Notification.user_id == citizen_user.id,
                Notification.notification_type == NotificationType.TICKET_STATUS_CHANGED,
            )
        )
        notification = result.scalar_one_or_none()

        assert notification is not None
        # Check for human-readable labels
        assert "In Progress" in notification.message
        assert "Resolved" in notification.message
