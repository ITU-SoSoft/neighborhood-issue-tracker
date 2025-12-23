"""Unit tests for API dependencies."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.api.deps import (
    get_current_user,
    get_current_active_user,
    get_current_verified_user,
    get_support_user,
    get_manager_user,
)
from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.models.user import User, UserRole


class TestGetCurrentUser:
    """Tests for get_current_user dependency."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def mock_credentials(self):
        """Create mock HTTP Bearer credentials."""
        credentials = MagicMock()
        credentials.credentials = "valid_token"
        return credentials

    @pytest.fixture
    def active_user(self):
        """Create an active user."""
        return User(
            id=uuid.uuid4(),
            phone_number="+905551234567",
            name="Test User",
            role=UserRole.CITIZEN,
            is_verified=True,
            is_active=True,
        )

    async def test_returns_user_with_valid_token(
        self, mock_db, mock_credentials, active_user
    ):
        """Should return user when token is valid."""
        from unittest.mock import patch

        # Mock token decoding
        with patch("app.api.deps.decode_token") as mock_decode:
            mock_decode.return_value = {"sub": str(active_user.id), "type": "access"}

            # Mock database query result
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = active_user
            mock_db.execute.return_value = mock_result

            result = await get_current_user(mock_credentials, mock_db)

            assert result == active_user
            mock_decode.assert_called_once_with("valid_token")

    async def test_raises_unauthorized_when_token_invalid(
        self, mock_db, mock_credentials
    ):
        """Should raise UnauthorizedException when token is invalid."""
        from unittest.mock import patch

        with patch("app.api.deps.decode_token") as mock_decode:
            mock_decode.return_value = None

            with pytest.raises(UnauthorizedException) as exc_info:
                await get_current_user(mock_credentials, mock_db)

            assert "Invalid or expired token" in str(exc_info.value.detail)

    async def test_raises_unauthorized_when_wrong_token_type(
        self, mock_db, mock_credentials
    ):
        """Should raise UnauthorizedException when token type is not 'access'."""
        from unittest.mock import patch

        with patch("app.api.deps.decode_token") as mock_decode:
            mock_decode.return_value = {"sub": str(uuid.uuid4()), "type": "refresh"}

            with pytest.raises(UnauthorizedException) as exc_info:
                await get_current_user(mock_credentials, mock_db)

            assert "Invalid token type" in str(exc_info.value.detail)

    async def test_raises_unauthorized_when_no_subject(self, mock_db, mock_credentials):
        """Should raise UnauthorizedException when token has no subject."""
        from unittest.mock import patch

        with patch("app.api.deps.decode_token") as mock_decode:
            mock_decode.return_value = {"type": "access"}

            with pytest.raises(UnauthorizedException) as exc_info:
                await get_current_user(mock_credentials, mock_db)

            assert "Invalid token payload" in str(exc_info.value.detail)

    async def test_raises_unauthorized_when_user_not_found(
        self, mock_db, mock_credentials
    ):
        """Should raise UnauthorizedException when user doesn't exist."""
        from unittest.mock import patch

        with patch("app.api.deps.decode_token") as mock_decode:
            mock_decode.return_value = {"sub": str(uuid.uuid4()), "type": "access"}

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result

            with pytest.raises(UnauthorizedException) as exc_info:
                await get_current_user(mock_credentials, mock_db)

            assert "User not found" in str(exc_info.value.detail)

    async def test_raises_unauthorized_when_user_inactive(
        self, mock_db, mock_credentials
    ):
        """Should raise UnauthorizedException when user is deactivated."""
        from unittest.mock import patch

        inactive_user = User(
            id=uuid.uuid4(),
            phone_number="+905551234567",
            name="Inactive User",
            role=UserRole.CITIZEN,
            is_verified=True,
            is_active=False,
        )

        with patch("app.api.deps.decode_token") as mock_decode:
            mock_decode.return_value = {"sub": str(inactive_user.id), "type": "access"}

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = inactive_user
            mock_db.execute.return_value = mock_result

            with pytest.raises(UnauthorizedException) as exc_info:
                await get_current_user(mock_credentials, mock_db)

            assert "deactivated" in str(exc_info.value.detail)


class TestGetCurrentActiveUser:
    """Tests for get_current_active_user dependency."""

    async def test_returns_active_user(self):
        """Should return user when active."""
        user = User(
            id=uuid.uuid4(),
            phone_number="+905551234567",
            name="Active User",
            role=UserRole.CITIZEN,
            is_active=True,
        )

        result = await get_current_active_user(user)
        assert result == user

    async def test_raises_forbidden_when_inactive(self):
        """Should raise ForbiddenException when user is inactive."""
        user = User(
            id=uuid.uuid4(),
            phone_number="+905551234567",
            name="Inactive User",
            role=UserRole.CITIZEN,
            is_active=False,
        )

        with pytest.raises(ForbiddenException) as exc_info:
            await get_current_active_user(user)

        assert "Inactive user" in str(exc_info.value.detail)


class TestGetCurrentVerifiedUser:
    """Tests for get_current_verified_user dependency."""

    async def test_returns_verified_user(self):
        """Should return user when verified."""
        user = User(
            id=uuid.uuid4(),
            phone_number="+905551234567",
            name="Verified User",
            role=UserRole.CITIZEN,
            is_verified=True,
        )

        result = await get_current_verified_user(user)
        assert result == user

    async def test_raises_forbidden_when_not_verified(self):
        """Should raise ForbiddenException when user is not verified."""
        user = User(
            id=uuid.uuid4(),
            phone_number="+905551234567",
            name="Unverified User",
            role=UserRole.CITIZEN,
            is_verified=False,
        )

        with pytest.raises(ForbiddenException) as exc_info:
            await get_current_verified_user(user)

        assert "not verified" in str(exc_info.value.detail)


class TestGetSupportUser:
    """Tests for get_support_user dependency."""

    async def test_returns_support_user(self):
        """Should return user when role is SUPPORT."""
        user = User(
            id=uuid.uuid4(),
            phone_number="+905551234567",
            name="Support User",
            role=UserRole.SUPPORT,
        )

        result = await get_support_user(user)
        assert result == user

    async def test_returns_manager_user(self):
        """Should return user when role is MANAGER (managers can do support tasks)."""
        user = User(
            id=uuid.uuid4(),
            phone_number="+905551234567",
            name="Manager User",
            role=UserRole.MANAGER,
        )

        result = await get_support_user(user)
        assert result == user

    async def test_raises_forbidden_for_citizen(self):
        """Should raise ForbiddenException for citizen role."""
        user = User(
            id=uuid.uuid4(),
            phone_number="+905551234567",
            name="Citizen User",
            role=UserRole.CITIZEN,
        )

        with pytest.raises(ForbiddenException) as exc_info:
            await get_support_user(user)

        assert "Support or manager role required" in str(exc_info.value.detail)


class TestGetManagerUser:
    """Tests for get_manager_user dependency."""

    async def test_returns_manager_user(self):
        """Should return user when role is MANAGER."""
        user = User(
            id=uuid.uuid4(),
            phone_number="+905551234567",
            name="Manager User",
            role=UserRole.MANAGER,
        )

        result = await get_manager_user(user)
        assert result == user

    async def test_raises_forbidden_for_support(self):
        """Should raise ForbiddenException for support role."""
        user = User(
            id=uuid.uuid4(),
            phone_number="+905551234567",
            name="Support User",
            role=UserRole.SUPPORT,
        )

        with pytest.raises(ForbiddenException) as exc_info:
            await get_manager_user(user)

        assert "Manager role required" in str(exc_info.value.detail)

    async def test_raises_forbidden_for_citizen(self):
        """Should raise ForbiddenException for citizen role."""
        user = User(
            id=uuid.uuid4(),
            phone_number="+905551234567",
            name="Citizen User",
            role=UserRole.CITIZEN,
        )

        with pytest.raises(ForbiddenException) as exc_info:
            await get_manager_user(user)

        assert "Manager role required" in str(exc_info.value.detail)
