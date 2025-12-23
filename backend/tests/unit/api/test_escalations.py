"""Unit tests for escalations API endpoints."""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.api.v1.escalations import (
    create_escalation,
    list_escalations,
    get_escalation,
    approve_escalation,
    reject_escalation,
)
from app.core.exceptions import (
    ForbiddenException,
    NotFoundException,
    TicketNotFoundException,
    EscalationAlreadyExistsException,
)
from app.models.user import User, UserRole
from app.models.team import Team
from app.models.ticket import Ticket, TicketStatus
from app.models.escalation import EscalationRequest, EscalationStatus
from app.schemas.escalation import EscalationCreate, EscalationReview


class TestCreateEscalation:
    """Tests for create_escalation endpoint."""

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
    def support_user(self):
        """Create a support user with team."""
        team_id = uuid.uuid4()
        return User(
            id=uuid.uuid4(),
            phone_number="+905551234567",
            name="Support",
            role=UserRole.SUPPORT,
            team_id=team_id,
        )

    async def test_create_escalation_success(self, mock_db, support_user):
        """Should create escalation for ticket assigned to user's team."""
        ticket_id = uuid.uuid4()
        ticket = Ticket(
            id=ticket_id,
            title="Test Ticket",
            status=TicketStatus.IN_PROGRESS,
            team_id=support_user.team_id,
            reporter_id=uuid.uuid4(),
        )

        escalation_data = EscalationCreate(
            ticket_id=ticket_id,
            reason="Need manager review for complex issue",
        )

        # Mock ticket lookup
        mock_ticket_result = MagicMock()
        mock_ticket_result.scalar_one_or_none.return_value = ticket

        # Mock existing escalations check
        mock_escalation_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_escalation_result.scalars.return_value = mock_scalars

        mock_db.execute.side_effect = [mock_ticket_result, mock_escalation_result]

        result = await create_escalation(escalation_data, support_user, mock_db)

        assert result.ticket_id == ticket_id
        assert result.status == EscalationStatus.PENDING
        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    async def test_create_escalation_ticket_not_found(self, mock_db, support_user):
        """Should raise TicketNotFoundException for non-existent ticket."""
        escalation_data = EscalationCreate(
            ticket_id=uuid.uuid4(),
            reason="Test reason",
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(TicketNotFoundException):
            await create_escalation(escalation_data, support_user, mock_db)

    async def test_create_escalation_not_assigned_to_team(self, mock_db, support_user):
        """Should raise ForbiddenException when ticket not assigned to team."""
        ticket = Ticket(
            id=uuid.uuid4(),
            title="Test Ticket",
            status=TicketStatus.IN_PROGRESS,
            team_id=None,  # Not assigned
            reporter_id=uuid.uuid4(),
        )

        escalation_data = EscalationCreate(
            ticket_id=ticket.id,
            reason="Test reason",
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = ticket
        mock_db.execute.return_value = mock_result

        with pytest.raises(ForbiddenException) as exc_info:
            await create_escalation(escalation_data, support_user, mock_db)

        assert "unassigned" in str(exc_info.value.detail).lower()

    async def test_create_escalation_different_team(self, mock_db, support_user):
        """Should raise ForbiddenException when ticket assigned to different team."""
        ticket = Ticket(
            id=uuid.uuid4(),
            title="Test Ticket",
            status=TicketStatus.IN_PROGRESS,
            team_id=uuid.uuid4(),  # Different team
            reporter_id=uuid.uuid4(),
        )

        escalation_data = EscalationCreate(
            ticket_id=ticket.id,
            reason="Test reason",
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = ticket
        mock_db.execute.return_value = mock_result

        with pytest.raises(ForbiddenException) as exc_info:
            await create_escalation(escalation_data, support_user, mock_db)

        assert "assigned to your team" in str(exc_info.value.detail)

    async def test_create_escalation_pending_exists(self, mock_db, support_user):
        """Should raise EscalationAlreadyExistsException when pending exists."""
        ticket = Ticket(
            id=uuid.uuid4(),
            title="Test Ticket",
            status=TicketStatus.IN_PROGRESS,
            team_id=support_user.team_id,
            reporter_id=uuid.uuid4(),
        )

        pending_escalation = EscalationRequest(
            id=uuid.uuid4(),
            ticket_id=ticket.id,
            status=EscalationStatus.PENDING,
        )

        escalation_data = EscalationCreate(
            ticket_id=ticket.id,
            reason="Test reason",
        )

        mock_ticket_result = MagicMock()
        mock_ticket_result.scalar_one_or_none.return_value = ticket

        mock_escalation_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [pending_escalation]
        mock_escalation_result.scalars.return_value = mock_scalars

        mock_db.execute.side_effect = [mock_ticket_result, mock_escalation_result]

        with pytest.raises(EscalationAlreadyExistsException):
            await create_escalation(escalation_data, support_user, mock_db)


class TestListEscalations:
    """Tests for list_escalations endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def support_user(self):
        """Create a support user with team."""
        return User(
            id=uuid.uuid4(),
            phone_number="+905551234567",
            name="Support",
            role=UserRole.SUPPORT,
            team_id=uuid.uuid4(),
        )

    @pytest.fixture
    def manager_user(self):
        """Create a manager user."""
        return User(
            id=uuid.uuid4(),
            phone_number="+905559999999",
            name="Manager",
            role=UserRole.MANAGER,
        )

    async def test_list_escalations_as_manager(self, mock_db, manager_user):
        """Manager should see all escalations."""
        escalation = EscalationRequest(
            id=uuid.uuid4(),
            ticket_id=uuid.uuid4(),
            requester_id=uuid.uuid4(),
            status=EscalationStatus.PENDING,
            reason="Test",
        )

        # Mock count
        mock_count = MagicMock()
        mock_count.scalar.return_value = 1

        # Mock escalations
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [escalation]
        mock_result.scalars.return_value = mock_scalars

        mock_db.execute.side_effect = [mock_count, mock_result]

        result = await list_escalations(
            manager_user,
            mock_db,
            status_filter=None,
            ticket_id=None,
            page=1,
            page_size=10,
        )

        assert result.total == 1
        assert len(result.items) == 1

    async def test_list_escalations_filter_by_status(self, mock_db, manager_user):
        """Should filter escalations by status."""
        mock_count = MagicMock()
        mock_count.scalar.return_value = 0

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars

        mock_db.execute.side_effect = [mock_count, mock_result]

        result = await list_escalations(
            manager_user,
            mock_db,
            status_filter=EscalationStatus.APPROVED,
            ticket_id=None,
            page=1,
            page_size=10,
        )

        assert result.total == 0


class TestGetEscalation:
    """Tests for get_escalation endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def support_user(self):
        """Create a support user."""
        return User(
            id=uuid.uuid4(),
            phone_number="+905551234567",
            name="Support",
            role=UserRole.SUPPORT,
        )

    async def test_get_escalation_success(self, mock_db, support_user):
        """Should return escalation by ID."""
        escalation_id = uuid.uuid4()
        escalation = EscalationRequest(
            id=escalation_id,
            ticket_id=uuid.uuid4(),
            requester_id=support_user.id,
            status=EscalationStatus.PENDING,
            reason="Test reason",
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = escalation
        mock_db.execute.return_value = mock_result

        result = await get_escalation(escalation_id, support_user, mock_db)

        assert result.id == escalation_id
        assert result.status == EscalationStatus.PENDING

    async def test_get_escalation_not_found(self, mock_db, support_user):
        """Should raise NotFoundException for non-existent escalation."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(NotFoundException):
            await get_escalation(uuid.uuid4(), support_user, mock_db)


class TestApproveEscalation:
    """Tests for approve_escalation endpoint."""

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
    def manager_user(self):
        """Create a manager user."""
        return User(
            id=uuid.uuid4(),
            phone_number="+905551234567",
            name="Manager",
            role=UserRole.MANAGER,
        )

    async def test_approve_escalation_success(self, mock_db, manager_user):
        """Should approve pending escalation."""
        escalation_id = uuid.uuid4()
        ticket = Ticket(
            id=uuid.uuid4(),
            title="Test Ticket",
            status=TicketStatus.ESCALATED,
        )
        escalation = EscalationRequest(
            id=escalation_id,
            ticket_id=ticket.id,
            requester_id=uuid.uuid4(),
            status=EscalationStatus.PENDING,
            reason="Need approval",
        )
        escalation.ticket = ticket

        review_data = EscalationReview(comment="Approved - proceed with fix")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = escalation
        mock_db.execute.return_value = mock_result

        result = await approve_escalation(
            escalation_id, review_data, manager_user, mock_db
        )

        assert result.status == EscalationStatus.APPROVED
        assert result.reviewer_id == manager_user.id
        mock_db.commit.assert_called()

    async def test_approve_escalation_not_found(self, mock_db, manager_user):
        """Should raise NotFoundException for non-existent escalation."""
        review_data = EscalationReview(comment="Approved")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(NotFoundException):
            await approve_escalation(uuid.uuid4(), review_data, manager_user, mock_db)

    async def test_approve_already_reviewed(self, mock_db, manager_user):
        """Should raise ForbiddenException for already reviewed escalation."""
        escalation = EscalationRequest(
            id=uuid.uuid4(),
            ticket_id=uuid.uuid4(),
            requester_id=uuid.uuid4(),
            status=EscalationStatus.APPROVED,  # Already approved
            reason="Test",
        )

        review_data = EscalationReview(comment="Try to approve again")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = escalation
        mock_db.execute.return_value = mock_result

        with pytest.raises(ForbiddenException):
            await approve_escalation(escalation.id, review_data, manager_user, mock_db)


class TestRejectEscalation:
    """Tests for reject_escalation endpoint."""

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
    def manager_user(self):
        """Create a manager user."""
        return User(
            id=uuid.uuid4(),
            phone_number="+905551234567",
            name="Manager",
            role=UserRole.MANAGER,
        )

    async def test_reject_escalation_success(self, mock_db, manager_user):
        """Should reject pending escalation."""
        escalation_id = uuid.uuid4()
        ticket = Ticket(
            id=uuid.uuid4(),
            title="Test Ticket",
            status=TicketStatus.ESCALATED,
        )
        escalation = EscalationRequest(
            id=escalation_id,
            ticket_id=ticket.id,
            requester_id=uuid.uuid4(),
            status=EscalationStatus.PENDING,
            reason="Need approval",
        )
        escalation.ticket = ticket

        review_data = EscalationReview(comment="Rejected - handle normally")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = escalation
        mock_db.execute.return_value = mock_result

        result = await reject_escalation(
            escalation_id, review_data, manager_user, mock_db
        )

        assert result.status == EscalationStatus.REJECTED
        assert result.reviewer_id == manager_user.id

    async def test_reject_escalation_not_found(self, mock_db, manager_user):
        """Should raise NotFoundException for non-existent escalation."""
        review_data = EscalationReview(comment="Rejected")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(NotFoundException):
            await reject_escalation(uuid.uuid4(), review_data, manager_user, mock_db)
