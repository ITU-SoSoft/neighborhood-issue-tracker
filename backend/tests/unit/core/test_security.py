"""Tests for security utilities."""

from datetime import timedelta, datetime, timezone

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_otp_code,
    get_otp_expiry,
    hash_password,
    verify_password,
)


class TestJWTTokens:
    """Tests for JWT token utilities."""

    def test_create_access_token(self):
        """Should create valid access token."""
        token = create_access_token(data={"sub": "user-123"})
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_expiry(self):
        """Should create access token with custom expiry."""
        token = create_access_token(
            data={"sub": "user-123"}, expires_delta=timedelta(minutes=30)
        )
        payload = decode_token(token)
        assert payload is not None
        assert payload.get("sub") == "user-123"

    def test_create_refresh_token(self):
        """Should create valid refresh token."""
        token = create_refresh_token(data={"sub": "user-123"})
        assert token is not None
        assert isinstance(token, str)

    def test_decode_valid_token(self):
        """Should decode valid token correctly."""
        token = create_access_token(data={"sub": "user-456"})
        payload = decode_token(token)
        assert payload is not None
        assert payload.get("sub") == "user-456"
        assert "exp" in payload

    def test_decode_invalid_token(self):
        """Should return None for invalid token."""
        payload = decode_token("invalid.token.here")
        assert payload is None

    def test_decode_expired_token(self):
        """Should return None for expired token."""
        token = create_access_token(
            data={"sub": "user-789"}, expires_delta=timedelta(seconds=-10)
        )
        payload = decode_token(token)
        assert payload is None


class TestOTPGeneration:
    """Tests for OTP generation utilities."""

    def test_generate_otp_code(self):
        """Should generate 6-digit OTP code."""
        code = generate_otp_code()
        assert code is not None
        assert len(code) == 6
        assert code.isdigit()

    def test_generate_otp_code_uniqueness(self):
        """Should generate different codes on each call."""
        codes = [generate_otp_code() for _ in range(100)]
        # While not guaranteed, with 6 digits we should have variety
        unique_codes = set(codes)
        assert len(unique_codes) > 50  # Should have at least 50% unique

    def test_get_otp_expiry(self):
        """Should return future datetime."""
        expiry = get_otp_expiry()
        assert expiry is not None
        assert expiry > datetime.now(timezone.utc)

    def test_get_otp_expiry_is_5_minutes(self):
        """OTP should expire in approximately 5 minutes."""
        now = datetime.now(timezone.utc)
        expiry = get_otp_expiry()
        diff = expiry - now
        # Allow 1 second tolerance
        assert 299 <= diff.total_seconds() <= 301


class TestPasswordHashing:
    """Tests for password hashing utilities."""

    def test_hash_password(self):
        """Should hash password successfully."""
        password = "SecurePassword123!"
        hashed = hash_password(password)

        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0
        # bcrypt hashes start with $2b$
        assert hashed.startswith("$2")

    def test_hash_password_produces_different_hashes(self):
        """Should produce different hashes for same password (different salts)."""
        password = "TestPassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2  # Different salts produce different hashes

    def test_verify_password_correct(self):
        """Should verify correct password."""
        password = "CorrectPassword123!"
        hashed = hash_password(password)

        result = verify_password(password, hashed)

        assert result is True

    def test_verify_password_incorrect(self):
        """Should reject incorrect password."""
        password = "CorrectPassword123!"
        wrong_password = "WrongPassword456!"
        hashed = hash_password(password)

        result = verify_password(wrong_password, hashed)

        assert result is False

    def test_verify_password_empty(self):
        """Should handle empty password."""
        password = ""
        hashed = hash_password(password)

        result = verify_password(password, hashed)

        assert result is True

    def test_hash_password_truncates_long_passwords(self):
        """Should handle passwords longer than bcrypt's 72 byte limit."""
        # Create a password longer than 72 bytes
        long_password = "a" * 100

        # Should not raise an error
        hashed = hash_password(long_password)

        # Should verify correctly (after truncation)
        assert verify_password(long_password, hashed) is True

    def test_hash_password_unicode(self):
        """Should handle unicode passwords."""
        password = "şifre123!Türkçe"
        hashed = hash_password(password)

        result = verify_password(password, hashed)

        assert result is True
