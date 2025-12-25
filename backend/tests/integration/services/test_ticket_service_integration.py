"""Integration tests for TicketService - tests the service layer with real database."""

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.district import District
from app.models.notification import Notification, NotificationType
from app.models.team import Team, TeamCategory, TeamDistrict
from app.models.ticket import StatusLog, Ticket, TicketFollower, TicketStatus
from app.models.user import User
from app.schemas.ticket import LocationCreate, TicketCreate, TicketUpdate
from app.services.ticket_service import TicketService


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def ticket_service() -> TicketService:
    """Create a TicketService instance."""
    return TicketService()


@pytest.fixture
async def district(db_session: AsyncSession) -> District:
    """Create a test district."""
    d = District(
        id=uuid.uuid4(),
        name="Kadikoy",
        city="Istanbul",
    )
    db_session.add(d)
    await db_session.commit()
    await db_session.refresh(d)
    return d


@pytest.fixture
async def team_with_category_and_district(
    db_session: AsyncSession, category: Category, district: District
) -> Team:
    """Create a team that handles a category in a specific district."""
    team = Team(
        id=uuid.uuid4(),
        name="Kadikoy Infrastructure Team",
        description="Handles infrastructure in Kadikoy",
    )
    db_session.add(team)
    await db_session.flush()

    # Link team to category (composite primary key: team_id + category_id)
    team_category = TeamCategory(
        team_id=team.id,
        category_id=category.id,
    )
    db_session.add(team_category)

    # Link team to district (composite primary key: team_id + district_id)
    team_district = TeamDistrict(
        team_id=team.id,
        district_id=district.id,
    )
    db_session.add(team_district)

    await db_session.commit()
    await db_session.refresh(team)
    return team


# ============================================================================
# Test: Create Ticket
# ============================================================================


class TestCreateTicket:
    """Tests for TicketService.create_ticket."""

    async def test_create_ticket_with_gps_coordinates(
        self,
        db_session: AsyncSession,
        ticket_service: TicketService,
        category: Category,
        citizen_user: User,
    ):
        """Should create a ticket with GPS coordinates."""
        request = TicketCreate(
            title="Pothole on Main Street",
            description="Large pothole causing traffic issues",
            category_id=category.id,
            location=LocationCreate(
                latitude=41.0082,
                longitude=28.9784,
                address="Main Street 123",
                city="Istanbul",
            ),
        )

        ticket = await ticket_service.create_ticket(db_session, request, citizen_user)

        assert ticket is not None
        assert ticket.title == "Pothole on Main Street"
        assert ticket.status == TicketStatus.NEW
        assert ticket.reporter_id == citizen_user.id
        assert ticket.location is not None
        assert ticket.location.latitude == 41.0082
        assert ticket.location.longitude == 28.9784

    async def test_create_ticket_with_district_id(
        self,
        db_session: AsyncSession,
        ticket_service: TicketService,
        category: Category,
        citizen_user: User,
        district: District,
    ):
        """Should create a ticket using district_id instead of GPS coordinates."""
        request = TicketCreate(
            title="Street Light Out",
            description="Street light not working",
            category_id=category.id,
            location=LocationCreate(
                district_id=district.id,
                address="District Center",
                city="Istanbul",
            ),
        )

        ticket = await ticket_service.create_ticket(db_session, request, citizen_user)

        assert ticket is not None
        assert ticket.location.district == "Kadikoy"
        assert ticket.location.city == "Istanbul"

    async def test_create_ticket_auto_assigns_team(
        self,
        db_session: AsyncSession,
        ticket_service: TicketService,
        category: Category,
        citizen_user: User,
        district: District,
        team_with_category_and_district: Team,
    ):
        """Should auto-assign ticket to matching team based on category and district."""
        request = TicketCreate(
            title="Infrastructure Issue",
            description="Road damage",
            category_id=category.id,
            location=LocationCreate(
                district_id=district.id,
                address="Kadikoy Center",
                city="Istanbul",
            ),
        )

        ticket = await ticket_service.create_ticket(db_session, request, citizen_user)

        assert ticket.team_id == team_with_category_and_district.id

    async def test_create_ticket_auto_follows_reporter(
        self,
        db_session: AsyncSession,
        ticket_service: TicketService,
        category: Category,
        citizen_user: User,
    ):
        """Should automatically add reporter as a follower of the ticket."""
        request = TicketCreate(
            title="Test Ticket",
            description="Testing auto-follow",
            category_id=category.id,
            location=LocationCreate(
                latitude=41.0082,
                longitude=28.9784,
                address="Test Address",
                city="Istanbul",
            ),
        )

        ticket = await ticket_service.create_ticket(db_session, request, citizen_user)

        # Check that reporter is a follower
        result = await db_session.execute(
            select(TicketFollower).where(
                TicketFollower.ticket_id == ticket.id,
                TicketFollower.user_id == citizen_user.id,
            )
        )
        follower = result.scalar_one_or_none()
        assert follower is not None

    async def test_create_ticket_creates_initial_status_log(
        self,
        db_session: AsyncSession,
        ticket_service: TicketService,
        category: Category,
        citizen_user: User,
    ):
        """Should create initial status log entry when ticket is created."""
        request = TicketCreate(
            title="Test Ticket",
            description="Testing status log",
            category_id=category.id,
            location=LocationCreate(
                latitude=41.0082,
                longitude=28.9784,
                address="Test Address",
                city="Istanbul",
            ),
        )

        ticket = await ticket_service.create_ticket(db_session, request, citizen_user)

        # Check status log was created
        result = await db_session.execute(
            select(StatusLog).where(StatusLog.ticket_id == ticket.id)
        )
        status_log = result.scalar_one_or_none()
        assert status_log is not None
        assert status_log.old_status is None
        assert status_log.new_status == "NEW"
        assert status_log.changed_by_id == citizen_user.id

    async def test_create_ticket_triggers_notification(
        self,
        db_session: AsyncSession,
        ticket_service: TicketService,
        category: Category,
        citizen_user: User,
    ):
        """Should create a notification when ticket is created."""
        request = TicketCreate(
            title="Notification Test Ticket",
            description="Testing notification creation",
            category_id=category.id,
            location=LocationCreate(
                latitude=41.0082,
                longitude=28.9784,
                address="Test Address",
                city="Istanbul",
            ),
        )

        ticket = await ticket_service.create_ticket(db_session, request, citizen_user)

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
        assert "Notification Test Ticket" in notification.message

    async def test_create_ticket_invalid_category_fails(
        self,
        db_session: AsyncSession,
        ticket_service: TicketService,
        citizen_user: User,
    ):
        """Should raise exception for invalid category."""
        from app.core.exceptions import CategoryNotFoundException

        request = TicketCreate(
            title="Test Ticket",
            description="Testing invalid category",
            category_id=uuid.uuid4(),  # Non-existent category
            location=LocationCreate(
                latitude=41.0082,
                longitude=28.9784,
                address="Test Address",
                city="Istanbul",
            ),
        )

        with pytest.raises(CategoryNotFoundException):
            await ticket_service.create_ticket(db_session, request, citizen_user)


# ============================================================================
# Test: Update Ticket
# ============================================================================


class TestUpdateTicket:
    """Tests for TicketService.update_ticket."""

    async def test_update_ticket_title_and_description(
        self,
        db_session: AsyncSession,
        ticket_service: TicketService,
        ticket: Ticket,
        citizen_user: User,
    ):
        """Reporter should be able to update ticket title and description."""
        # Need to set ticket to NEW status for citizen to update
        ticket.status = TicketStatus.NEW
        await db_session.commit()

        request = TicketUpdate(
            title="Updated Title",
            description="Updated description",
        )

        updated = await ticket_service.update_ticket(
            db_session, ticket, request, citizen_user
        )

        assert updated.title == "Updated Title"
        assert updated.description == "Updated description"

    async def test_update_ticket_change_category(
        self,
        db_session: AsyncSession,
        ticket_service: TicketService,
        ticket: Ticket,
        citizen_user: User,
    ):
        """Should allow changing ticket category."""
        ticket.status = TicketStatus.NEW
        await db_session.commit()

        # Create a new category to change to (avoid fixture conflicts)
        new_category = Category(
            id=uuid.uuid4(),
            name="Traffic Issues",
            description="Traffic related problems",
            is_active=True,
        )
        db_session.add(new_category)
        await db_session.commit()

        request = TicketUpdate(category_id=new_category.id)

        updated = await ticket_service.update_ticket(
            db_session, ticket, request, citizen_user
        )

        assert updated.category_id == new_category.id

    async def test_citizen_cannot_update_non_new_ticket(
        self,
        db_session: AsyncSession,
        ticket_service: TicketService,
        ticket: Ticket,
        citizen_user: User,
    ):
        """Citizen should not be able to update ticket that is not NEW."""
        from app.core.exceptions import ForbiddenException

        ticket.status = TicketStatus.IN_PROGRESS
        await db_session.commit()

        request = TicketUpdate(title="Attempted Update")

        with pytest.raises(ForbiddenException):
            await ticket_service.update_ticket(
                db_session, ticket, request, citizen_user
            )

    async def test_staff_can_update_in_progress_ticket(
        self,
        db_session: AsyncSession,
        ticket_service: TicketService,
        ticket: Ticket,
        support_user: User,
    ):
        """Support staff should be able to update IN_PROGRESS ticket."""
        ticket.status = TicketStatus.IN_PROGRESS
        await db_session.commit()

        request = TicketUpdate(title="Staff Updated Title")

        updated = await ticket_service.update_ticket(
            db_session, ticket, request, support_user
        )

        assert updated.title == "Staff Updated Title"


# ============================================================================
# Test: Update Status
# ============================================================================


class TestUpdateStatus:
    """Tests for TicketService.update_status."""

    async def test_update_status_creates_status_log(
        self,
        db_session: AsyncSession,
        ticket_service: TicketService,
        ticket: Ticket,
        support_user: User,
    ):
        """Should create status log entry on status change."""
        ticket.status = TicketStatus.NEW
        await db_session.commit()

        await ticket_service.update_status(
            db_session,
            ticket,
            TicketStatus.IN_PROGRESS,
            comment="Starting work on this ticket",
            current_user=support_user,
        )

        # Check status log was created
        result = await db_session.execute(
            select(StatusLog)
            .where(StatusLog.ticket_id == ticket.id)
            .order_by(StatusLog.created_at.desc())
        )
        status_log = result.scalars().first()
        assert status_log is not None
        assert status_log.old_status == "NEW"
        assert status_log.new_status == "IN_PROGRESS"
        assert status_log.comment == "Starting work on this ticket"

    async def test_update_status_to_resolved_sets_resolved_at(
        self,
        db_session: AsyncSession,
        ticket_service: TicketService,
        ticket: Ticket,
        support_user: User,
    ):
        """Should set resolved_at timestamp when status changes to RESOLVED."""
        ticket.status = TicketStatus.IN_PROGRESS
        await db_session.commit()

        updated = await ticket_service.update_status(
            db_session,
            ticket,
            TicketStatus.RESOLVED,
            comment="Issue fixed",
            current_user=support_user,
        )

        assert updated.resolved_at is not None

    async def test_update_status_invalid_transition_fails(
        self,
        db_session: AsyncSession,
        ticket_service: TicketService,
        ticket: Ticket,
        support_user: User,
    ):
        """Should raise exception for invalid status transition."""
        from app.core.exceptions import InvalidStatusTransitionException

        ticket.status = TicketStatus.NEW
        await db_session.commit()

        # NEW -> CLOSED is not a valid transition
        with pytest.raises(InvalidStatusTransitionException):
            await ticket_service.update_status(
                db_session,
                ticket,
                TicketStatus.CLOSED,
                comment=None,
                current_user=support_user,
            )

    async def test_update_status_notifies_reporter(
        self,
        db_session: AsyncSession,
        ticket_service: TicketService,
        ticket: Ticket,
        support_user: User,
        citizen_user: User,
    ):
        """Should notify reporter when status changes (if changed by someone else)."""
        ticket.status = TicketStatus.NEW
        ticket.reporter_id = citizen_user.id
        await db_session.commit()

        await ticket_service.update_status(
            db_session,
            ticket,
            TicketStatus.IN_PROGRESS,
            comment="Working on it",
            current_user=support_user,
        )

        # Check notification was created for reporter
        result = await db_session.execute(
            select(Notification).where(
                Notification.user_id == citizen_user.id,
                Notification.ticket_id == ticket.id,
                Notification.notification_type
                == NotificationType.TICKET_STATUS_CHANGED,
            )
        )
        notification = result.scalar_one_or_none()
        assert notification is not None


# ============================================================================
# Test: Assign Ticket
# ============================================================================


class TestAssignTicket:
    """Tests for TicketService.assign_ticket."""

    async def test_assign_ticket_to_team(
        self,
        db_session: AsyncSession,
        ticket_service: TicketService,
        unassigned_ticket: Ticket,
        team: Team,
    ):
        """Should assign ticket to a team."""
        updated = await ticket_service.assign_ticket(
            db_session, unassigned_ticket, team.id
        )

        assert updated.team_id == team.id

    async def test_reassign_ticket_to_different_team(
        self,
        db_session: AsyncSession,
        ticket_service: TicketService,
        ticket: Ticket,
        other_team: Team,
    ):
        """Should allow reassigning ticket to a different team."""
        original_team_id = ticket.team_id

        updated = await ticket_service.assign_ticket(db_session, ticket, other_team.id)

        assert updated.team_id == other_team.id
        assert updated.team_id != original_team_id

    async def test_assign_ticket_nonexistent_team_fails(
        self,
        db_session: AsyncSession,
        ticket_service: TicketService,
        unassigned_ticket: Ticket,
    ):
        """Should raise exception when assigning to non-existent team."""
        from app.core.exceptions import NotFoundException

        with pytest.raises(NotFoundException):
            await ticket_service.assign_ticket(
                db_session, unassigned_ticket, uuid.uuid4()
            )
