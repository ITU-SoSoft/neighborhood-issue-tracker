"""Tests for security utilities."""

import pytest
from datetime import timedelta, datetime, timezone

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_otp_code,
    get_otp_expiry,
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
