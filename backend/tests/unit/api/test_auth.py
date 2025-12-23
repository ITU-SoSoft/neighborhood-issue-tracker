"""Unit tests for authentication API endpoints."""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.v1.auth import (
    request_otp,
    verify_otp,
    register,
    login,
    staff_login,
    refresh_token,
    get_current_user_info,
)
from app.core.exceptions import (
    OTPExpiredException,
    OTPInvalidException,
    UserAlreadyExistsException,
    EmailAlreadyExistsException,
    InvalidCredentialsException,
    UserNotVerifiedException,
    NotStaffException,
)
from app.models.user import User, UserRole, OTPCode
from app.schemas.auth import (
    RequestOTPRequest,
    VerifyOTPRequest,
    RegisterRequest,
    LoginRequest,
    StaffLoginRequest,
    RefreshTokenRequest,
)


class TestRequestOTP:
    """Tests for request_otp endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def mock_request(self):
        """Create a mock FastAPI request."""
        request = MagicMock()
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        return request

    async def test_request_otp_for_new_phone(self, mock_db, mock_request):
        """Should generate OTP for new phone number."""
        otp_request = RequestOTPRequest(phone_number="+905551234567")

        # Mock: no existing verified user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with patch("app.api.v1.auth.check_rate_limit", new_callable=AsyncMock):
            with patch("app.api.v1.auth.sms_service") as mock_sms:
                mock_sms.send_otp = AsyncMock(return_value=True)

                result = await request_otp(otp_request, mock_db, mock_request)

                assert result.message == "OTP code sent successfully"
                assert result.expires_in_seconds == 300

    async def test_request_otp_for_existing_verified_user(self, mock_db, mock_request):
        """Should raise UserAlreadyExistsException for verified user."""
        otp_request = RequestOTPRequest(phone_number="+905551234567")

        # Mock: existing verified user
        existing_user = User(
            id=uuid.uuid4(),
            phone_number="+905551234567",
            is_verified=True,
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_user
        mock_db.execute.return_value = mock_result

        with patch("app.api.v1.auth.check_rate_limit", new_callable=AsyncMock):
            with pytest.raises(UserAlreadyExistsException):
                await request_otp(otp_request, mock_db, mock_request)


class TestVerifyOTP:
    """Tests for verify_otp endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.execute = AsyncMock()
        return db

    async def test_verify_valid_otp_new_user(self, mock_db):
        """Should create new user and return tokens for valid OTP."""
        verify_request = VerifyOTPRequest(phone_number="+905551234567", code="123456")

        # Mock: valid OTP
        valid_otp = OTPCode(
            id=uuid.uuid4(),
            phone_number="+905551234567",
            code="123456",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
            is_used=False,
        )

        # First call returns OTP, second returns None (no existing user)
        mock_result1 = MagicMock()
        mock_result1.scalar_one_or_none.return_value = valid_otp
        mock_result2 = MagicMock()
        mock_result2.scalar_one_or_none.return_value = None

        mock_db.execute.side_effect = [mock_result1, mock_result2]

        with patch("app.api.v1.auth.create_access_token") as mock_access:
            with patch("app.api.v1.auth.create_refresh_token") as mock_refresh:
                mock_access.return_value = "access_token"
                mock_refresh.return_value = "refresh_token"

                result = await verify_otp(verify_request, mock_db)

                assert result.access_token == "access_token"
                assert result.refresh_token == "refresh_token"
                assert result.token_type == "bearer"
                mock_db.add.assert_called()

    async def test_verify_otp_invalid_code(self, mock_db):
        """Should raise OTPInvalidException for wrong code."""
        verify_request = VerifyOTPRequest(phone_number="+905551234567", code="000000")

        # Mock: no OTP found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(OTPInvalidException):
            await verify_otp(verify_request, mock_db)

    async def test_verify_otp_expired(self, mock_db):
        """Should raise OTPExpiredException for expired OTP."""
        verify_request = VerifyOTPRequest(phone_number="+905551234567", code="123456")

        # Mock: expired OTP
        expired_otp = OTPCode(
            id=uuid.uuid4(),
            phone_number="+905551234567",
            code="123456",
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=5),
            is_used=False,
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = expired_otp
        mock_db.execute.return_value = mock_result

        with pytest.raises(OTPExpiredException):
            await verify_otp(verify_request, mock_db)


class TestRegister:
    """Tests for register endpoint."""

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
    def mock_request(self):
        """Create a mock FastAPI request."""
        request = MagicMock()
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        return request

    async def test_register_success(self, mock_db, mock_request):
        """Should create user and return tokens on successful registration."""
        register_request = RegisterRequest(
            phone_number="+905551234567",
            email="test@example.com",
            password="SecurePass123!",
            full_name="Test User",
        )

        # Mock: no existing users
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with patch("app.api.v1.auth.check_rate_limit", new_callable=AsyncMock):
            with patch("app.api.v1.auth.hash_password") as mock_hash:
                with patch("app.api.v1.auth.create_access_token") as mock_access:
                    with patch("app.api.v1.auth.create_refresh_token") as mock_refresh:
                        mock_hash.return_value = "hashed_password"
                        mock_access.return_value = "access_token"
                        mock_refresh.return_value = "refresh_token"

                        result = await register(register_request, mock_db, mock_request)

                        assert result.access_token == "access_token"
                        assert result.token_type == "bearer"
                        mock_db.add.assert_called_once()

    async def test_register_phone_already_exists(self, mock_db, mock_request):
        """Should raise UserAlreadyExistsException for existing phone."""
        register_request = RegisterRequest(
            phone_number="+905551234567",
            email="test@example.com",
            password="SecurePass123!",
            full_name="Test User",
        )

        # Mock: existing user with phone
        existing_user = User(
            id=uuid.uuid4(),
            phone_number="+905551234567",
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_user
        mock_db.execute.return_value = mock_result

        with patch("app.api.v1.auth.check_rate_limit", new_callable=AsyncMock):
            with pytest.raises(UserAlreadyExistsException):
                await register(register_request, mock_db, mock_request)

    async def test_register_email_already_exists(self, mock_db, mock_request):
        """Should raise EmailAlreadyExistsException for existing email."""
        register_request = RegisterRequest(
            phone_number="+905551234567",
            email="test@example.com",
            password="SecurePass123!",
            full_name="Test User",
        )

        # First call: no user with phone, second call: user with email
        mock_result1 = MagicMock()
        mock_result1.scalar_one_or_none.return_value = None
        mock_result2 = MagicMock()
        mock_result2.scalar_one_or_none.return_value = User(
            id=uuid.uuid4(),
            email="test@example.com",
        )
        mock_db.execute.side_effect = [mock_result1, mock_result2]

        with patch("app.api.v1.auth.check_rate_limit", new_callable=AsyncMock):
            with pytest.raises(EmailAlreadyExistsException):
                await register(register_request, mock_db, mock_request)


class TestLogin:
    """Tests for login endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def mock_request(self):
        """Create a mock FastAPI request."""
        request = MagicMock()
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        return request

    async def test_login_success(self, mock_db, mock_request):
        """Should return tokens on successful login."""
        login_request = LoginRequest(
            email="test@example.com",
            password="SecurePass123!",
        )

        verified_user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            password_hash="hashed_password",
            is_verified=True,
            is_active=True,
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = verified_user
        mock_db.execute.return_value = mock_result

        with patch("app.api.v1.auth.check_rate_limit", new_callable=AsyncMock):
            with patch("app.api.v1.auth.verify_password") as mock_verify:
                with patch("app.api.v1.auth.create_access_token") as mock_access:
                    with patch("app.api.v1.auth.create_refresh_token") as mock_refresh:
                        mock_verify.return_value = True
                        mock_access.return_value = "access_token"
                        mock_refresh.return_value = "refresh_token"

                        result = await login(login_request, mock_db, mock_request)

                        assert result.access_token == "access_token"
                        assert result.token_type == "bearer"

    async def test_login_invalid_credentials(self, mock_db, mock_request):
        """Should raise InvalidCredentialsException for wrong credentials."""
        login_request = LoginRequest(
            email="test@example.com",
            password="WrongPassword",
        )

        # Mock: no user found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with patch("app.api.v1.auth.check_rate_limit", new_callable=AsyncMock):
            with pytest.raises(InvalidCredentialsException):
                await login(login_request, mock_db, mock_request)

    async def test_login_wrong_password(self, mock_db, mock_request):
        """Should raise InvalidCredentialsException for wrong password."""
        login_request = LoginRequest(
            email="test@example.com",
            password="WrongPassword",
        )

        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            password_hash="hashed_password",
            is_verified=True,
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user
        mock_db.execute.return_value = mock_result

        with patch("app.api.v1.auth.check_rate_limit", new_callable=AsyncMock):
            with patch("app.api.v1.auth.verify_password") as mock_verify:
                mock_verify.return_value = False

                with pytest.raises(InvalidCredentialsException):
                    await login(login_request, mock_db, mock_request)

    async def test_login_unverified_user(self, mock_db, mock_request):
        """Should raise UserNotVerifiedException for unverified user."""
        login_request = LoginRequest(
            email="test@example.com",
            password="SecurePass123!",
        )

        unverified_user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            password_hash="hashed_password",
            is_verified=False,
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = unverified_user
        mock_db.execute.return_value = mock_result

        with patch("app.api.v1.auth.check_rate_limit", new_callable=AsyncMock):
            with pytest.raises(UserNotVerifiedException):
                await login(login_request, mock_db, mock_request)


class TestStaffLogin:
    """Tests for staff_login endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def mock_request(self):
        """Create a mock FastAPI request."""
        request = MagicMock()
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        return request

    async def test_staff_login_success(self, mock_db, mock_request):
        """Should return tokens for staff user."""
        login_request = StaffLoginRequest(
            email="support@example.com",
            password="SecurePass123!",
        )

        support_user = User(
            id=uuid.uuid4(),
            email="support@example.com",
            password_hash="hashed_password",
            role=UserRole.SUPPORT,
            is_verified=True,
            is_active=True,
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = support_user
        mock_db.execute.return_value = mock_result

        with patch("app.api.v1.auth.check_rate_limit", new_callable=AsyncMock):
            with patch("app.api.v1.auth.verify_password") as mock_verify:
                with patch("app.api.v1.auth.create_access_token") as mock_access:
                    with patch("app.api.v1.auth.create_refresh_token") as mock_refresh:
                        mock_verify.return_value = True
                        mock_access.return_value = "access_token"
                        mock_refresh.return_value = "refresh_token"

                        result = await staff_login(login_request, mock_db, mock_request)

                        assert result.access_token == "access_token"

    async def test_staff_login_citizen_rejected(self, mock_db, mock_request):
        """Should raise NotStaffException for citizen users."""
        login_request = StaffLoginRequest(
            email="citizen@example.com",
            password="SecurePass123!",
        )

        citizen_user = User(
            id=uuid.uuid4(),
            email="citizen@example.com",
            password_hash="hashed_password",
            role=UserRole.CITIZEN,
            is_verified=True,
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = citizen_user
        mock_db.execute.return_value = mock_result

        with patch("app.api.v1.auth.check_rate_limit", new_callable=AsyncMock):
            with patch("app.api.v1.auth.verify_password") as mock_verify:
                mock_verify.return_value = True

                with pytest.raises(NotStaffException):
                    await staff_login(login_request, mock_db, mock_request)

    async def test_staff_login_unverified(self, mock_db, mock_request):
        """Should raise UserNotVerifiedException for unverified staff."""
        login_request = StaffLoginRequest(
            email="support@example.com",
            password="SecurePass123!",
        )

        unverified_staff = User(
            id=uuid.uuid4(),
            email="support@example.com",
            password_hash="hashed_password",
            role=UserRole.SUPPORT,
            is_verified=False,
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = unverified_staff
        mock_db.execute.return_value = mock_result

        with patch("app.api.v1.auth.check_rate_limit", new_callable=AsyncMock):
            with pytest.raises(UserNotVerifiedException):
                await staff_login(login_request, mock_db, mock_request)


class TestRefreshToken:
    """Tests for refresh_token endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        return db

    async def test_refresh_token_success(self, mock_db):
        """Should return new tokens for valid refresh token."""
        user_id = uuid.uuid4()
        refresh_request = RefreshTokenRequest(refresh_token="valid_refresh_token")

        user = User(
            id=user_id,
            phone_number="+905551234567",
            is_active=True,
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user
        mock_db.execute.return_value = mock_result

        with patch("app.api.v1.auth.decode_token") as mock_decode:
            with patch("app.api.v1.auth.create_access_token") as mock_access:
                with patch("app.api.v1.auth.create_refresh_token") as mock_refresh:
                    mock_decode.return_value = {"sub": str(user_id), "type": "refresh"}
                    mock_access.return_value = "new_access_token"
                    mock_refresh.return_value = "new_refresh_token"

                    result = await refresh_token(refresh_request, mock_db)

                    assert result.access_token == "new_access_token"
                    assert result.token_type == "bearer"

    async def test_refresh_token_invalid(self, mock_db):
        """Should raise OTPInvalidException for invalid refresh token."""
        refresh_request = RefreshTokenRequest(refresh_token="invalid_token")

        with patch("app.api.v1.auth.decode_token") as mock_decode:
            mock_decode.return_value = None

            with pytest.raises(OTPInvalidException):
                await refresh_token(refresh_request, mock_db)

    async def test_refresh_token_wrong_type(self, mock_db):
        """Should raise OTPInvalidException for access token used as refresh."""
        refresh_request = RefreshTokenRequest(refresh_token="access_token")

        with patch("app.api.v1.auth.decode_token") as mock_decode:
            mock_decode.return_value = {"sub": str(uuid.uuid4()), "type": "access"}

            with pytest.raises(OTPInvalidException):
                await refresh_token(refresh_request, mock_db)


class TestGetCurrentUserInfo:
    """Tests for get_current_user_info endpoint."""

    async def test_returns_user_info(self):
        """Should return current user's information."""
        now = datetime.now(timezone.utc)
        user = User(
            id=uuid.uuid4(),
            phone_number="+905551234567",
            name="Test User",
            email="test@example.com",
            role=UserRole.CITIZEN,
            is_verified=True,
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        result = await get_current_user_info(user)

        assert result.id == user.id
        assert result.phone_number == user.phone_number
        assert result.name == user.name
        assert result.email == user.email
        assert result.role == user.role
