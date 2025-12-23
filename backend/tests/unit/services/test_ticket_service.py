"""Unit tests for TicketService."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import (
    CategoryNotFoundException,
    ForbiddenException,
    InvalidStatusTransitionException,
    NotFoundException,
)
from app.models.category import Category
from app.models.ticket import Ticket, TicketStatus
from app.models.user import User, UserRole
from app.schemas.ticket import LocationCreate, TicketCreate, TicketUpdate
from app.services.ticket_service import TicketService


class TestTicketServiceCreate:
    """Tests for TicketService.create_ticket method."""

    @pytest.fixture
    def ticket_service(self):
        """Create a TicketService instance."""
        return TicketService()

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def citizen_user(self):
        """Create a test citizen user."""
        return User(
            id=uuid.uuid4(),
            phone_number="+905551234567",
            name="Test Citizen",
            email="citizen@test.com",
            role=UserRole.CITIZEN,
            is_verified=True,
            is_active=True,
        )

    @pytest.fixture
    def category(self):
        """Create a test category."""
        return Category(
            id=uuid.uuid4(),
            name="Infrastructure",
            description="Infrastructure issues",
            is_active=True,
        )

    @pytest.fixture
    def ticket_create_request(self, category):
        """Create a ticket creation request."""
        return TicketCreate(
            title="Test Ticket Title",
            description="This is a test ticket description that is long enough.",
            category_id=category.id,
            location=LocationCreate(
                latitude=41.0082,
                longitude=28.9784,
                address="Test Address",
                city="Istanbul",
            ),
        )

    async def test_create_ticket_validates_category_exists(
        self, ticket_service, mock_db, citizen_user, ticket_create_request
    ):
        """Should raise CategoryNotFoundException when category doesn't exist."""
        # Mock category lookup to return None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(CategoryNotFoundException):
            await ticket_service.create_ticket(
                mock_db, ticket_create_request, citizen_user
            )

    async def test_create_ticket_validates_category_is_active(
        self, ticket_service, mock_db, citizen_user, ticket_create_request
    ):
        """Should raise CategoryNotFoundException when category is inactive."""
        # Mock category lookup to return None (since query filters by is_active=True)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(CategoryNotFoundException):
            await ticket_service.create_ticket(
                mock_db, ticket_create_request, citizen_user
            )


class TestTicketServiceUpdate:
    """Tests for TicketService.update_ticket method."""

    @pytest.fixture
    def ticket_service(self):
        """Create a TicketService instance."""
        return TicketService()

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def citizen_user(self):
        """Create a test citizen user."""
        user_id = uuid.uuid4()
        return User(
            id=user_id,
            phone_number="+905551234567",
            name="Test Citizen",
            email="citizen@test.com",
            role=UserRole.CITIZEN,
            is_verified=True,
            is_active=True,
        )

    @pytest.fixture
    def support_user(self):
        """Create a test support user."""
        return User(
            id=uuid.uuid4(),
            phone_number="+905559876543",
            name="Test Support",
            email="support@test.com",
            role=UserRole.SUPPORT,
            is_verified=True,
            is_active=True,
        )

    @pytest.fixture
    def new_ticket(self, citizen_user):
        """Create a NEW ticket owned by citizen_user."""
        return Ticket(
            id=uuid.uuid4(),
            title="Test Ticket",
            description="Test description",
            status=TicketStatus.NEW,
            reporter_id=citizen_user.id,
            category_id=uuid.uuid4(),
            location_id=uuid.uuid4(),
        )

    @pytest.fixture
    def in_progress_ticket(self, citizen_user):
        """Create an IN_PROGRESS ticket owned by citizen_user."""
        return Ticket(
            id=uuid.uuid4(),
            title="Test Ticket",
            description="Test description",
            status=TicketStatus.IN_PROGRESS,
            reporter_id=citizen_user.id,
            category_id=uuid.uuid4(),
            location_id=uuid.uuid4(),
        )

    @pytest.fixture
    def closed_ticket(self, citizen_user):
        """Create a CLOSED ticket owned by citizen_user."""
        return Ticket(
            id=uuid.uuid4(),
            title="Test Ticket",
            description="Test description",
            status=TicketStatus.CLOSED,
            reporter_id=citizen_user.id,
            category_id=uuid.uuid4(),
            location_id=uuid.uuid4(),
        )

    async def test_citizen_can_update_own_new_ticket(
        self, ticket_service, mock_db, citizen_user, new_ticket
    ):
        """Citizen should be able to update their own NEW ticket."""
        update_request = TicketUpdate(title="Updated Title Here")

        result = await ticket_service.update_ticket(
            mock_db, new_ticket, update_request, citizen_user
        )

        assert result.title == "Updated Title Here"
        mock_db.commit.assert_called_once()

    async def test_citizen_cannot_update_non_new_ticket(
        self, ticket_service, mock_db, citizen_user, in_progress_ticket
    ):
        """Citizen should not be able to update IN_PROGRESS tickets."""
        update_request = TicketUpdate(title="Updated Title Here")

        with pytest.raises(ForbiddenException) as exc_info:
            await ticket_service.update_ticket(
                mock_db, in_progress_ticket, update_request, citizen_user
            )

        assert "still NEW" in str(exc_info.value.detail)

    async def test_citizen_cannot_update_others_ticket(
        self, ticket_service, mock_db, new_ticket
    ):
        """Citizen should not be able to update another user's ticket."""
        other_user = User(
            id=uuid.uuid4(),
            phone_number="+905557778899",
            name="Other User",
            role=UserRole.CITIZEN,
        )
        update_request = TicketUpdate(title="Updated Title Here")

        with pytest.raises(ForbiddenException) as exc_info:
            await ticket_service.update_ticket(
                mock_db, new_ticket, update_request, other_user
            )

        assert "permission" in str(exc_info.value.detail).lower()

    async def test_support_can_update_any_ticket(
        self, ticket_service, mock_db, support_user, in_progress_ticket
    ):
        """Support user should be able to update any non-closed ticket."""
        update_request = TicketUpdate(
            description="Updated description that is long enough for validation"
        )

        result = await ticket_service.update_ticket(
            mock_db, in_progress_ticket, update_request, support_user
        )

        assert (
            result.description
            == "Updated description that is long enough for validation"
        )
        mock_db.commit.assert_called_once()

    async def test_nobody_can_update_closed_ticket(
        self, ticket_service, mock_db, support_user, closed_ticket
    ):
        """No one should be able to update a CLOSED ticket."""
        update_request = TicketUpdate(title="Updated Title Here")

        with pytest.raises(ForbiddenException) as exc_info:
            await ticket_service.update_ticket(
                mock_db, closed_ticket, update_request, support_user
            )

        assert "closed" in str(exc_info.value.detail).lower()

    async def test_update_with_invalid_category_fails(
        self, ticket_service, mock_db, citizen_user, new_ticket
    ):
        """Should raise CategoryNotFoundException when updating to invalid category."""
        update_request = TicketUpdate(category_id=uuid.uuid4())

        # Mock category lookup to return None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(CategoryNotFoundException):
            await ticket_service.update_ticket(
                mock_db, new_ticket, update_request, citizen_user
            )


class TestTicketServiceUpdateStatus:
    """Tests for TicketService.update_status method."""

    @pytest.fixture
    def ticket_service(self):
        """Create a TicketService instance."""
        return TicketService()

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        return db

    @pytest.fixture
    def support_user(self):
        """Create a test support user."""
        return User(
            id=uuid.uuid4(),
            phone_number="+905559876543",
            name="Test Support",
            email="support@test.com",
            role=UserRole.SUPPORT,
            is_verified=True,
            is_active=True,
        )

    @pytest.fixture
    def new_ticket(self):
        """Create a NEW ticket."""
        return Ticket(
            id=uuid.uuid4(),
            title="Test Ticket",
            description="Test description",
            status=TicketStatus.NEW,
            reporter_id=uuid.uuid4(),
            category_id=uuid.uuid4(),
            location_id=uuid.uuid4(),
        )

    @pytest.fixture
    def in_progress_ticket(self):
        """Create an IN_PROGRESS ticket."""
        return Ticket(
            id=uuid.uuid4(),
            title="Test Ticket",
            description="Test description",
            status=TicketStatus.IN_PROGRESS,
            reporter_id=uuid.uuid4(),
            category_id=uuid.uuid4(),
            location_id=uuid.uuid4(),
        )

    @pytest.fixture
    def resolved_ticket(self):
        """Create a RESOLVED ticket."""
        return Ticket(
            id=uuid.uuid4(),
            title="Test Ticket",
            description="Test description",
            status=TicketStatus.RESOLVED,
            reporter_id=uuid.uuid4(),
            category_id=uuid.uuid4(),
            location_id=uuid.uuid4(),
        )

    @pytest.fixture
    def closed_ticket(self):
        """Create a CLOSED ticket."""
        return Ticket(
            id=uuid.uuid4(),
            title="Test Ticket",
            description="Test description",
            status=TicketStatus.CLOSED,
            reporter_id=uuid.uuid4(),
            category_id=uuid.uuid4(),
            location_id=uuid.uuid4(),
        )

    # Valid transitions
    @patch(
        "app.services.notification_service.notify_ticket_status_changed",
        new_callable=AsyncMock,
    )
    async def test_new_to_in_progress(
        self, mock_notify, ticket_service, mock_db, support_user, new_ticket
    ):
        """NEW -> IN_PROGRESS is a valid transition."""
        result = await ticket_service.update_status(
            mock_db, new_ticket, TicketStatus.IN_PROGRESS, None, support_user
        )

        assert result.status == TicketStatus.IN_PROGRESS
        mock_db.add.assert_called_once()  # StatusLog added
        mock_db.commit.assert_called_once()

    @patch(
        "app.services.notification_service.notify_ticket_status_changed",
        new_callable=AsyncMock,
    )
    async def test_in_progress_to_resolved(
        self, mock_notify, ticket_service, mock_db, support_user, in_progress_ticket
    ):
        """IN_PROGRESS -> RESOLVED is a valid transition."""
        result = await ticket_service.update_status(
            mock_db,
            in_progress_ticket,
            TicketStatus.RESOLVED,
            "Issue fixed",
            support_user,
        )

        assert result.status == TicketStatus.RESOLVED
        assert result.resolved_at is not None

    @patch(
        "app.services.notification_service.notify_ticket_status_changed",
        new_callable=AsyncMock,
    )
    async def test_resolved_to_closed(
        self, mock_notify, ticket_service, mock_db, support_user, resolved_ticket
    ):
        """RESOLVED -> CLOSED is a valid transition."""
        result = await ticket_service.update_status(
            mock_db, resolved_ticket, TicketStatus.CLOSED, None, support_user
        )

        assert result.status == TicketStatus.CLOSED

    @patch(
        "app.services.notification_service.notify_ticket_status_changed",
        new_callable=AsyncMock,
    )
    async def test_resolved_to_in_progress_reopen(
        self, mock_notify, ticket_service, mock_db, support_user, resolved_ticket
    ):
        """RESOLVED -> IN_PROGRESS (reopen) is a valid transition."""
        result = await ticket_service.update_status(
            mock_db,
            resolved_ticket,
            TicketStatus.IN_PROGRESS,
            "Reopening",
            support_user,
        )

        assert result.status == TicketStatus.IN_PROGRESS

    @patch(
        "app.services.notification_service.notify_ticket_status_changed",
        new_callable=AsyncMock,
    )
    async def test_new_to_escalated(
        self, mock_notify, ticket_service, mock_db, support_user, new_ticket
    ):
        """NEW -> ESCALATED is a valid transition."""
        result = await ticket_service.update_status(
            mock_db,
            new_ticket,
            TicketStatus.ESCALATED,
            "Needs manager review",
            support_user,
        )

        assert result.status == TicketStatus.ESCALATED

    # Invalid transitions
    async def test_new_cannot_jump_to_resolved(
        self, ticket_service, mock_db, support_user, new_ticket
    ):
        """NEW -> RESOLVED is NOT a valid transition."""
        with pytest.raises(InvalidStatusTransitionException):
            await ticket_service.update_status(
                mock_db, new_ticket, TicketStatus.RESOLVED, None, support_user
            )

    async def test_new_cannot_jump_to_closed(
        self, ticket_service, mock_db, support_user, new_ticket
    ):
        """NEW -> CLOSED is NOT a valid transition."""
        with pytest.raises(InvalidStatusTransitionException):
            await ticket_service.update_status(
                mock_db, new_ticket, TicketStatus.CLOSED, None, support_user
            )

    async def test_closed_cannot_change(
        self, ticket_service, mock_db, support_user, closed_ticket
    ):
        """CLOSED tickets cannot transition to any other state."""
        with pytest.raises(InvalidStatusTransitionException):
            await ticket_service.update_status(
                mock_db, closed_ticket, TicketStatus.IN_PROGRESS, None, support_user
            )

    async def test_in_progress_cannot_jump_to_closed(
        self, ticket_service, mock_db, support_user, in_progress_ticket
    ):
        """IN_PROGRESS -> CLOSED is NOT a valid transition (must resolve first)."""
        with pytest.raises(InvalidStatusTransitionException):
            await ticket_service.update_status(
                mock_db, in_progress_ticket, TicketStatus.CLOSED, None, support_user
            )

    @patch(
        "app.services.notification_service.notify_ticket_status_changed",
        new_callable=AsyncMock,
    )
    async def test_status_change_creates_log_entry(
        self, mock_notify, ticket_service, mock_db, support_user, new_ticket
    ):
        """Status change should create a StatusLog entry."""
        await ticket_service.update_status(
            mock_db, new_ticket, TicketStatus.IN_PROGRESS, "Starting work", support_user
        )

        # Verify db.add was called (for StatusLog)
        mock_db.add.assert_called_once()
        status_log = mock_db.add.call_args[0][0]
        assert status_log.old_status == TicketStatus.NEW.value
        assert status_log.new_status == TicketStatus.IN_PROGRESS.value
        assert status_log.comment == "Starting work"
        assert status_log.changed_by_id == support_user.id


class TestTicketServiceAssign:
    """Tests for TicketService.assign_ticket method."""

    @pytest.fixture
    def ticket_service(self):
        """Create a TicketService instance."""
        return TicketService()

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def unassigned_ticket(self):
        """Create an unassigned ticket."""
        return Ticket(
            id=uuid.uuid4(),
            title="Test Ticket",
            description="Test description",
            status=TicketStatus.NEW,
            reporter_id=uuid.uuid4(),
            category_id=uuid.uuid4(),
            location_id=uuid.uuid4(),
            team_id=None,
        )

    async def test_assign_ticket_to_valid_team(
        self, ticket_service, mock_db, unassigned_ticket
    ):
        """Should successfully assign ticket to a valid team."""
        from app.models.team import Team

        team = Team(id=uuid.uuid4(), name="Test Team")

        # Mock team lookup to return the team
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = team
        mock_db.execute.return_value = mock_result

        result = await ticket_service.assign_ticket(mock_db, unassigned_ticket, team.id)

        assert result.team_id == team.id
        mock_db.commit.assert_called_once()

    async def test_assign_ticket_to_nonexistent_team_fails(
        self, ticket_service, mock_db, unassigned_ticket
    ):
        """Should raise NotFoundException when assigning to nonexistent team."""
        # Mock team lookup to return None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(NotFoundException) as exc_info:
            await ticket_service.assign_ticket(mock_db, unassigned_ticket, uuid.uuid4())

        assert "Team" in str(exc_info.value.detail)
