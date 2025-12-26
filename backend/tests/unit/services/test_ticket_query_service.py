"""Tests for ticket query service utilities."""

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from app.models.ticket import Ticket, TicketStatus
from app.models.user import User, UserRole
from app.models.escalation import EscalationStatus
from app.services.ticket_query_service import (
    VALID_TRANSITIONS,
    build_ticket_response,
    build_ticket_detail_response,
)


class TestValidTransitions:
    """Tests for status transition rules."""

    def test_new_can_transition_to_in_progress(self):
        """NEW tickets can transition to IN_PROGRESS."""
        assert TicketStatus.IN_PROGRESS in VALID_TRANSITIONS[TicketStatus.NEW]

    def test_new_can_transition_to_escalated(self):
        """NEW tickets can transition to ESCALATED."""
        assert TicketStatus.ESCALATED in VALID_TRANSITIONS[TicketStatus.NEW]

    def test_in_progress_can_transition_to_resolved(self):
        """IN_PROGRESS tickets can transition to RESOLVED."""
        assert TicketStatus.RESOLVED in VALID_TRANSITIONS[TicketStatus.IN_PROGRESS]

    def test_in_progress_can_transition_to_escalated(self):
        """IN_PROGRESS tickets can transition to ESCALATED."""
        assert TicketStatus.ESCALATED in VALID_TRANSITIONS[TicketStatus.IN_PROGRESS]

    def test_escalated_can_transition_to_in_progress(self):
        """ESCALATED tickets can transition back to IN_PROGRESS."""
        assert TicketStatus.IN_PROGRESS in VALID_TRANSITIONS[TicketStatus.ESCALATED]

    def test_resolved_can_transition_to_closed(self):
        """RESOLVED tickets can transition to CLOSED."""
        assert TicketStatus.CLOSED in VALID_TRANSITIONS[TicketStatus.RESOLVED]

    def test_resolved_can_transition_to_in_progress(self):
        """RESOLVED tickets can be reopened (IN_PROGRESS)."""
        assert TicketStatus.IN_PROGRESS in VALID_TRANSITIONS[TicketStatus.RESOLVED]

    def test_closed_can_transition_to_in_progress(self):
        """CLOSED tickets can transition back to IN_PROGRESS."""
        assert TicketStatus.IN_PROGRESS in VALID_TRANSITIONS[TicketStatus.CLOSED]


def create_mock_location():
    """Create a valid LocationResponse-compatible mock."""
    location = MagicMock()
    location.id = uuid.uuid4()
    location.latitude = 41.0082
    location.longitude = 28.9784
    location.address = "123 Test St"
    location.district = "Kadikoy"
    location.city = "Istanbul"
    return location


class TestBuildTicketResponse:
    """Tests for build_ticket_response function."""

    @pytest.fixture
    def mock_user(self):
        """Create a mock user."""
        user = MagicMock(spec=User)
        user.id = uuid.uuid4()
        user.role = UserRole.CITIZEN
        user.name = "Test User"
        return user

    @pytest.fixture
    def mock_ticket(self, mock_user):
        """Create a mock ticket with relationships."""
        ticket = MagicMock(spec=Ticket)
        ticket.id = uuid.uuid4()
        ticket.title = "Test Ticket"
        ticket.description = "Test description"
        ticket.status = TicketStatus.NEW
        ticket.category_id = uuid.uuid4()
        ticket.reporter_id = mock_user.id
        ticket.team_id = None
        ticket.resolved_at = None
        ticket.created_at = datetime.now(timezone.utc)
        ticket.updated_at = datetime.now(timezone.utc)

        # Mock category relationship
        ticket.category = MagicMock()
        ticket.category.name = "Infrastructure"

        # Mock location with proper values
        ticket.location = create_mock_location()

        # Mock reporter relationship
        ticket.reporter = MagicMock()
        ticket.reporter.name = "Reporter Name"

        # Mock assigned_team relationship
        ticket.assigned_team = None

        # Mock collections
        ticket.photos = []
        ticket.comments = []
        ticket.followers = []

        return ticket

    def test_build_ticket_response_basic(self, mock_ticket, mock_user):
        """Should build a basic ticket response."""
        response = build_ticket_response(mock_ticket, mock_user)

        assert response.id == mock_ticket.id
        assert response.title == "Test Ticket"
        assert response.description == "Test description"
        assert response.status == TicketStatus.NEW
        assert response.category_name == "Infrastructure"
        assert response.reporter_name == "Reporter Name"

    def test_build_ticket_response_with_photos(self, mock_ticket, mock_user):
        """Should count photos correctly."""
        mock_ticket.photos = [MagicMock(), MagicMock(), MagicMock()]

        response = build_ticket_response(mock_ticket, mock_user)

        assert response.photo_count == 3

    def test_build_ticket_response_with_comments(self, mock_ticket, mock_user):
        """Should count comments correctly."""
        mock_ticket.comments = [MagicMock(), MagicMock()]

        response = build_ticket_response(mock_ticket, mock_user)

        assert response.comment_count == 2

    def test_build_ticket_response_with_followers(self, mock_ticket, mock_user):
        """Should count followers correctly."""
        mock_ticket.followers = [MagicMock(), MagicMock(), MagicMock(), MagicMock()]

        response = build_ticket_response(mock_ticket, mock_user)

        assert response.follower_count == 4

    def test_build_ticket_response_with_team(self, mock_ticket, mock_user):
        """Should include team name when assigned."""
        mock_ticket.team_id = uuid.uuid4()
        mock_ticket.assigned_team = MagicMock()
        mock_ticket.assigned_team.name = "Infrastructure Team"

        response = build_ticket_response(mock_ticket, mock_user)

        assert response.team_name == "Infrastructure Team"

    def test_build_ticket_response_no_category(self, mock_ticket, mock_user):
        """Should handle missing category gracefully."""
        mock_ticket.category = None

        response = build_ticket_response(mock_ticket, mock_user)

        assert response.category_name is None

    def test_build_ticket_response_no_reporter(self, mock_ticket, mock_user):
        """Should handle missing reporter gracefully."""
        mock_ticket.reporter = None

        response = build_ticket_response(mock_ticket, mock_user)

        assert response.reporter_name is None


class TestBuildTicketDetailResponse:
    """Tests for build_ticket_detail_response function."""

    @pytest.fixture
    def mock_citizen(self):
        """Create a mock citizen user."""
        user = MagicMock(spec=User)
        user.id = uuid.uuid4()
        user.role = UserRole.CITIZEN
        user.name = "Citizen User"
        return user

    @pytest.fixture
    def mock_support(self):
        """Create a mock support user."""
        user = MagicMock(spec=User)
        user.id = uuid.uuid4()
        user.role = UserRole.SUPPORT
        user.name = "Support User"
        return user

    @pytest.fixture
    def mock_detail_ticket(self, mock_citizen):
        """Create a mock ticket with full relationships for detail view."""
        ticket = MagicMock(spec=Ticket)
        ticket.id = uuid.uuid4()
        ticket.title = "Detailed Test Ticket"
        ticket.description = "Detailed description"
        ticket.status = TicketStatus.IN_PROGRESS
        ticket.category_id = uuid.uuid4()
        ticket.reporter_id = mock_citizen.id
        ticket.team_id = uuid.uuid4()
        ticket.resolved_at = None
        ticket.created_at = datetime.now(timezone.utc)
        ticket.updated_at = datetime.now(timezone.utc)

        # Mock relationships
        ticket.category = MagicMock()
        ticket.category.name = "Roads"

        # Mock location with proper values
        ticket.location = create_mock_location()

        ticket.reporter = MagicMock()
        ticket.reporter.name = "John Citizen"

        ticket.assigned_team = MagicMock()
        ticket.assigned_team.name = "Roads Team"

        # Empty collections by default
        ticket.photos = []
        ticket.comments = []
        ticket.followers = []
        ticket.status_logs = []
        ticket.feedback = None
        ticket.escalations = []

        return ticket

    def test_build_detail_response_basic(self, mock_detail_ticket, mock_citizen):
        """Should build a detailed ticket response."""
        response = build_ticket_detail_response(mock_detail_ticket, mock_citizen)

        assert response.id == mock_detail_ticket.id
        assert response.title == "Detailed Test Ticket"
        assert response.team_name == "Roads Team"

    def test_build_detail_response_is_following_true(
        self, mock_detail_ticket, mock_citizen
    ):
        """Should correctly identify when user is following."""
        follower = MagicMock()
        follower.user_id = mock_citizen.id
        mock_detail_ticket.followers = [follower]

        response = build_ticket_detail_response(mock_detail_ticket, mock_citizen)

        assert response.is_following is True

    def test_build_detail_response_is_following_false(
        self, mock_detail_ticket, mock_citizen
    ):
        """Should correctly identify when user is not following."""
        other_follower = MagicMock()
        other_follower.user_id = uuid.uuid4()  # Different user
        mock_detail_ticket.followers = [other_follower]

        response = build_ticket_detail_response(mock_detail_ticket, mock_citizen)

        assert response.is_following is False

    def test_build_detail_response_filters_internal_comments_for_citizen(
        self, mock_detail_ticket, mock_citizen
    ):
        """Should filter out internal comments for citizens."""
        public_comment = MagicMock()
        public_comment.id = uuid.uuid4()
        public_comment.ticket_id = mock_detail_ticket.id
        public_comment.user_id = uuid.uuid4()
        public_comment.content = "Public comment"
        public_comment.is_internal = False
        public_comment.created_at = datetime.now(timezone.utc)
        public_comment.user = MagicMock()
        public_comment.user.name = "Commenter"

        internal_comment = MagicMock()
        internal_comment.id = uuid.uuid4()
        internal_comment.ticket_id = mock_detail_ticket.id
        internal_comment.user_id = uuid.uuid4()
        internal_comment.content = "Internal note"
        internal_comment.is_internal = True
        internal_comment.created_at = datetime.now(timezone.utc)
        internal_comment.user = MagicMock()
        internal_comment.user.name = "Staff"

        mock_detail_ticket.comments = [public_comment, internal_comment]

        response = build_ticket_detail_response(mock_detail_ticket, mock_citizen)

        assert response.comment_count == 1
        assert len(response.comments) == 1
        assert response.comments[0].content == "Public comment"

    def test_build_detail_response_shows_internal_comments_for_support(
        self, mock_detail_ticket, mock_support
    ):
        """Should show internal comments for support users."""
        public_comment = MagicMock()
        public_comment.id = uuid.uuid4()
        public_comment.ticket_id = mock_detail_ticket.id
        public_comment.user_id = uuid.uuid4()
        public_comment.content = "Public comment"
        public_comment.is_internal = False
        public_comment.created_at = datetime.now(timezone.utc)
        public_comment.user = MagicMock()
        public_comment.user.name = "Commenter"

        internal_comment = MagicMock()
        internal_comment.id = uuid.uuid4()
        internal_comment.ticket_id = mock_detail_ticket.id
        internal_comment.user_id = uuid.uuid4()
        internal_comment.content = "Internal note"
        internal_comment.is_internal = True
        internal_comment.created_at = datetime.now(timezone.utc)
        internal_comment.user = MagicMock()
        internal_comment.user.name = "Staff"

        mock_detail_ticket.comments = [public_comment, internal_comment]

        response = build_ticket_detail_response(mock_detail_ticket, mock_support)

        assert response.comment_count == 2
        assert len(response.comments) == 2

    def test_build_detail_response_has_feedback(self, mock_detail_ticket, mock_citizen):
        """Should correctly identify when ticket has feedback."""
        mock_detail_ticket.feedback = MagicMock()

        response = build_ticket_detail_response(mock_detail_ticket, mock_citizen)

        assert response.has_feedback is True

    def test_build_detail_response_no_feedback(self, mock_detail_ticket, mock_citizen):
        """Should correctly identify when ticket has no feedback."""
        mock_detail_ticket.feedback = None

        response = build_ticket_detail_response(mock_detail_ticket, mock_citizen)

        assert response.has_feedback is False

    def test_build_detail_response_has_escalation(
        self, mock_detail_ticket, mock_citizen
    ):
        """Should correctly identify when ticket has escalations."""
        escalation = MagicMock()
        escalation.status = EscalationStatus.PENDING
        mock_detail_ticket.escalations = [escalation]

        response = build_ticket_detail_response(mock_detail_ticket, mock_citizen)

        assert response.has_escalation is True

    def test_build_detail_response_can_escalate_when_no_pending(
        self, mock_detail_ticket, mock_citizen
    ):
        """Should allow escalation when no pending/approved escalations exist."""
        mock_detail_ticket.team_id = uuid.uuid4()
        mock_detail_ticket.escalations = []

        response = build_ticket_detail_response(mock_detail_ticket, mock_citizen)

        assert response.can_escalate is True

    def test_build_detail_response_cannot_escalate_when_pending(
        self, mock_detail_ticket, mock_citizen
    ):
        """Should not allow escalation when pending escalation exists."""
        mock_detail_ticket.team_id = uuid.uuid4()
        pending_escalation = MagicMock()
        pending_escalation.status = EscalationStatus.PENDING
        mock_detail_ticket.escalations = [pending_escalation]

        response = build_ticket_detail_response(mock_detail_ticket, mock_citizen)

        assert response.can_escalate is False

    def test_build_detail_response_cannot_escalate_when_approved(
        self, mock_detail_ticket, mock_citizen
    ):
        """Should not allow escalation when approved escalation exists."""
        mock_detail_ticket.team_id = uuid.uuid4()
        approved_escalation = MagicMock()
        approved_escalation.status = EscalationStatus.APPROVED
        mock_detail_ticket.escalations = [approved_escalation]

        response = build_ticket_detail_response(mock_detail_ticket, mock_citizen)

        assert response.can_escalate is False

    def test_build_detail_response_cannot_escalate_without_team(
        self, mock_detail_ticket, mock_citizen
    ):
        """Should not allow escalation when no team is assigned."""
        mock_detail_ticket.team_id = None
        mock_detail_ticket.escalations = []

        response = build_ticket_detail_response(mock_detail_ticket, mock_citizen)

        assert response.can_escalate is False

    def test_build_detail_response_status_logs(self, mock_detail_ticket, mock_citizen):
        """Should include status logs in response."""
        status_log = MagicMock()
        status_log.id = uuid.uuid4()
        status_log.ticket_id = mock_detail_ticket.id
        status_log.old_status = "new"
        status_log.new_status = "in_progress"
        status_log.changed_by_id = uuid.uuid4()
        status_log.changed_by = MagicMock()
        status_log.changed_by.name = "Staff User"
        status_log.comment = "Starting work"
        status_log.created_at = datetime.now(timezone.utc)

        mock_detail_ticket.status_logs = [status_log]

        response = build_ticket_detail_response(mock_detail_ticket, mock_citizen)

        assert len(response.status_logs) == 1
        assert response.status_logs[0].new_status == "in_progress"
        assert response.status_logs[0].changed_by_name == "Staff User"
