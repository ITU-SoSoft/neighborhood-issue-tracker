"""Unit tests for feedback API endpoints."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.api.v1.feedback import submit_feedback, get_feedback
from app.core.exceptions import (
    FeedbackAlreadyExistsException,
    ForbiddenException,
    TicketNotFoundException,
)
from app.models.feedback import Feedback
from app.models.ticket import Ticket, TicketStatus
from app.models.user import User, UserRole
from app.schemas.feedback import FeedbackCreate


class TestSubmitFeedback:
    """Tests for submit_feedback endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.add = MagicMock()
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

    async def test_submit_feedback_success(self, mock_db, citizen_user):
        """Should submit feedback for a resolved ticket."""
        ticket_id = uuid.uuid4()
        ticket = MagicMock(spec=Ticket)
        ticket.id = ticket_id
        ticket.reporter_id = citizen_user.id
        ticket.status = TicketStatus.RESOLVED
        ticket.feedback = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = ticket
        mock_db.execute.return_value = mock_result

        request = FeedbackCreate(rating=5, comment="Great service!")

        async def mock_refresh(feedback):
            feedback.id = uuid.uuid4()
            feedback.created_at = datetime.now(timezone.utc)

        mock_db.refresh = mock_refresh

        result = await submit_feedback(ticket_id, request, citizen_user, mock_db)

        assert result.rating == 5
        assert result.comment == "Great service!"
        assert result.user_name == citizen_user.name
        mock_db.add.assert_called_once()

    async def test_submit_feedback_closed_ticket(self, mock_db, citizen_user):
        """Should submit feedback for a closed ticket."""
        ticket_id = uuid.uuid4()
        ticket = MagicMock(spec=Ticket)
        ticket.id = ticket_id
        ticket.reporter_id = citizen_user.id
        ticket.status = TicketStatus.CLOSED
        ticket.feedback = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = ticket
        mock_db.execute.return_value = mock_result

        request = FeedbackCreate(rating=4, comment="Good!")

        async def mock_refresh(feedback):
            feedback.id = uuid.uuid4()
            feedback.created_at = datetime.now(timezone.utc)

        mock_db.refresh = mock_refresh

        result = await submit_feedback(ticket_id, request, citizen_user, mock_db)

        assert result.rating == 4

    async def test_submit_feedback_ticket_not_found(self, mock_db, citizen_user):
        """Should raise TicketNotFoundException when ticket doesn't exist."""
        ticket_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        request = FeedbackCreate(rating=5)

        with pytest.raises(TicketNotFoundException):
            await submit_feedback(ticket_id, request, citizen_user, mock_db)

    async def test_submit_feedback_not_reporter(self, mock_db, citizen_user):
        """Should raise ForbiddenException when user is not the reporter."""
        ticket_id = uuid.uuid4()
        ticket = MagicMock(spec=Ticket)
        ticket.id = ticket_id
        ticket.reporter_id = uuid.uuid4()  # Different user
        ticket.status = TicketStatus.RESOLVED
        ticket.feedback = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = ticket
        mock_db.execute.return_value = mock_result

        request = FeedbackCreate(rating=5)

        with pytest.raises(ForbiddenException) as exc_info:
            await submit_feedback(ticket_id, request, citizen_user, mock_db)

        assert "reporter" in str(exc_info.value.detail)

    async def test_submit_feedback_wrong_status(self, mock_db, citizen_user):
        """Should raise ForbiddenException when ticket is not resolved/closed."""
        ticket_id = uuid.uuid4()
        ticket = MagicMock(spec=Ticket)
        ticket.id = ticket_id
        ticket.reporter_id = citizen_user.id
        ticket.status = TicketStatus.IN_PROGRESS
        ticket.feedback = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = ticket
        mock_db.execute.return_value = mock_result

        request = FeedbackCreate(rating=5)

        with pytest.raises(ForbiddenException) as exc_info:
            await submit_feedback(ticket_id, request, citizen_user, mock_db)

        assert "resolved" in str(exc_info.value.detail)

    async def test_submit_feedback_already_exists(self, mock_db, citizen_user):
        """Should raise FeedbackAlreadyExistsException when feedback exists."""
        ticket_id = uuid.uuid4()
        ticket = MagicMock(spec=Ticket)
        ticket.id = ticket_id
        ticket.reporter_id = citizen_user.id
        ticket.status = TicketStatus.RESOLVED
        ticket.feedback = Feedback(id=uuid.uuid4(), rating=5)  # Already has feedback

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = ticket
        mock_db.execute.return_value = mock_result

        request = FeedbackCreate(rating=3)

        with pytest.raises(FeedbackAlreadyExistsException):
            await submit_feedback(ticket_id, request, citizen_user, mock_db)


class TestGetFeedback:
    """Tests for get_feedback endpoint."""

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

    async def test_get_feedback_success(self, mock_db, citizen_user):
        """Should return feedback for a ticket."""
        ticket_id = uuid.uuid4()
        user = User(id=uuid.uuid4(), name="Feedback User")
        now = datetime.now(timezone.utc)

        feedback = MagicMock(spec=Feedback)
        feedback.id = uuid.uuid4()
        feedback.ticket_id = ticket_id
        feedback.user_id = user.id
        feedback.user = user
        feedback.rating = 5
        feedback.comment = "Excellent!"
        feedback.created_at = now

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = feedback
        mock_db.execute.return_value = mock_result

        result = await get_feedback(ticket_id, citizen_user, mock_db)

        assert result.rating == 5
        assert result.comment == "Excellent!"
        assert result.user_name == "Feedback User"

    async def test_get_feedback_not_found(self, mock_db, citizen_user):
        """Should raise TicketNotFoundException when feedback doesn't exist."""
        ticket_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(TicketNotFoundException):
            await get_feedback(ticket_id, citizen_user, mock_db)
