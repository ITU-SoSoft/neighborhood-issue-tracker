"""Unit tests for comments API endpoints."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.api.v1.comments import list_comments, create_comment
from app.core.exceptions import ForbiddenException, TicketNotFoundException
from app.models.comment import Comment
from app.models.ticket import Ticket
from app.models.user import User, UserRole
from app.schemas.comment import CommentCreate


class TestListComments:
    """Tests for list_comments endpoint."""

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

    @pytest.fixture
    def support_user(self):
        """Create a mock support user."""
        return User(
            id=uuid.uuid4(),
            phone_number="+905559876543",
            name="Support User",
            role=UserRole.SUPPORT,
        )

    async def test_list_comments_citizen_only_public(self, mock_db, citizen_user):
        """Citizens should only see public comments."""
        ticket_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        # Mock ticket exists
        mock_ticket_result = MagicMock()
        mock_ticket_result.scalar_one_or_none.return_value = Ticket(id=ticket_id)

        # Mock comments - only public (citizens shouldn't see internal)
        user_obj = User(id=uuid.uuid4(), name="Commenter")
        public_comment = MagicMock(spec=Comment)
        public_comment.id = uuid.uuid4()
        public_comment.ticket_id = ticket_id
        public_comment.user_id = user_obj.id
        public_comment.user = user_obj
        public_comment.content = "Public comment"
        public_comment.is_internal = False
        public_comment.created_at = now

        mock_comments_result = MagicMock()
        mock_comments_scalars = MagicMock()
        mock_comments_scalars.all.return_value = [public_comment]
        mock_comments_result.scalars.return_value = mock_comments_scalars

        mock_db.execute.side_effect = [mock_ticket_result, mock_comments_result]

        result = await list_comments(ticket_id, citizen_user, mock_db)

        assert result.total == 1
        assert result.items[0].is_internal is False

    async def test_list_comments_support_sees_all(self, mock_db, support_user):
        """Support users should see all comments including internal."""
        ticket_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        # Mock ticket exists
        mock_ticket_result = MagicMock()
        mock_ticket_result.scalar_one_or_none.return_value = Ticket(id=ticket_id)

        user_obj = User(id=uuid.uuid4(), name="Commenter")

        public_comment = MagicMock(spec=Comment)
        public_comment.id = uuid.uuid4()
        public_comment.ticket_id = ticket_id
        public_comment.user_id = user_obj.id
        public_comment.user = user_obj
        public_comment.content = "Public comment"
        public_comment.is_internal = False
        public_comment.created_at = now

        internal_comment = MagicMock(spec=Comment)
        internal_comment.id = uuid.uuid4()
        internal_comment.ticket_id = ticket_id
        internal_comment.user_id = user_obj.id
        internal_comment.user = user_obj
        internal_comment.content = "Internal note"
        internal_comment.is_internal = True
        internal_comment.created_at = now

        mock_comments_result = MagicMock()
        mock_comments_scalars = MagicMock()
        mock_comments_scalars.all.return_value = [public_comment, internal_comment]
        mock_comments_result.scalars.return_value = mock_comments_scalars

        mock_db.execute.side_effect = [mock_ticket_result, mock_comments_result]

        result = await list_comments(ticket_id, support_user, mock_db)

        assert result.total == 2

    async def test_list_comments_ticket_not_found(self, mock_db, citizen_user):
        """Should raise TicketNotFoundException when ticket doesn't exist."""
        ticket_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(TicketNotFoundException):
            await list_comments(ticket_id, citizen_user, mock_db)


class TestCreateComment:
    """Tests for create_comment endpoint."""

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

    @pytest.fixture
    def support_user(self):
        """Create a mock support user."""
        return User(
            id=uuid.uuid4(),
            phone_number="+905559876543",
            name="Support User",
            role=UserRole.SUPPORT,
        )

    async def test_create_public_comment_success(self, mock_db, citizen_user):
        """Should create a public comment."""
        ticket_id = uuid.uuid4()
        request = CommentCreate(content="This is my comment", is_internal=False)

        # Mock ticket exists
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = Ticket(id=ticket_id)
        mock_db.execute.return_value = mock_result

        async def mock_refresh(comment):
            comment.id = uuid.uuid4()
            comment.created_at = datetime.now(timezone.utc)

        mock_db.refresh = mock_refresh

        result = await create_comment(ticket_id, request, citizen_user, mock_db)

        assert result.content == "This is my comment"
        assert result.is_internal is False
        assert result.user_name == citizen_user.name
        mock_db.add.assert_called_once()

    async def test_create_internal_comment_by_support(self, mock_db, support_user):
        """Support should be able to create internal comments."""
        ticket_id = uuid.uuid4()
        request = CommentCreate(content="Internal note", is_internal=True)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = Ticket(id=ticket_id)
        mock_db.execute.return_value = mock_result

        async def mock_refresh(comment):
            comment.id = uuid.uuid4()
            comment.created_at = datetime.now(timezone.utc)

        mock_db.refresh = mock_refresh

        result = await create_comment(ticket_id, request, support_user, mock_db)

        assert result.is_internal is True

    async def test_citizen_cannot_create_internal_comment(self, mock_db, citizen_user):
        """Citizens should not be able to create internal comments."""
        ticket_id = uuid.uuid4()
        request = CommentCreate(content="Trying internal", is_internal=True)

        with pytest.raises(ForbiddenException):
            await create_comment(ticket_id, request, citizen_user, mock_db)

    async def test_create_comment_ticket_not_found(self, mock_db, citizen_user):
        """Should raise TicketNotFoundException when ticket doesn't exist."""
        ticket_id = uuid.uuid4()
        request = CommentCreate(content="Comment", is_internal=False)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(TicketNotFoundException):
            await create_comment(ticket_id, request, citizen_user, mock_db)
