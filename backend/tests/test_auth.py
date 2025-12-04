"""Tests for authentication endpoints."""

import pytest
from httpx import AsyncClient

from app.models import User


class TestRequestOTP:
    """Tests for POST /api/v1/auth/request-otp."""

    async def test_request_otp_valid_phone(self, client: AsyncClient):
        """Should successfully request OTP for valid Turkish phone number."""
        response = await client.post(
            "/api/v1/auth/request-otp",
            json={"phone_number": "+905551234567"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["expires_in_seconds"] == 300  # 5 minutes

    async def test_request_otp_invalid_phone(self, client: AsyncClient):
        """Should reject invalid phone number format."""
        response = await client.post(
            "/api/v1/auth/request-otp",
            json={"phone_number": "invalid"},
        )
        assert response.status_code == 422

    async def test_request_otp_non_turkish_phone(self, client: AsyncClient):
        """Should reject non-Turkish phone numbers."""
        response = await client.post(
            "/api/v1/auth/request-otp",
            json={"phone_number": "+12025551234"},  # US number
        )
        assert response.status_code == 422


class TestVerifyOTP:
    """Tests for POST /api/v1/auth/verify-otp."""

    async def test_verify_otp_invalid_code(self, client: AsyncClient):
        """Should reject invalid OTP code."""
        response = await client.post(
            "/api/v1/auth/verify-otp",
            json={"phone_number": "+905551234567", "code": "000000"},
        )
        # Either 400 (invalid OTP) or 404 (OTP not found)
        assert response.status_code in [400, 404]


class TestLogin:
    """Tests for POST /api/v1/auth/login."""

    async def test_login_verified_user(self, client: AsyncClient, citizen_user: User):
        """Should login verified user successfully."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"phone_number": citizen_user.phone_number},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "user_id" in data

    async def test_login_unverified_user(
        self, client: AsyncClient, unverified_user: User
    ):
        """Should reject login for unverified user."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"phone_number": unverified_user.phone_number},
        )
        # 401 Unauthorized - user must complete verification first
        assert response.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Should reject login for nonexistent user."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"phone_number": "+905559999999"},
        )
        assert response.status_code == 404


class TestGetCurrentUser:
    """Tests for GET /api/v1/auth/me."""

    async def test_get_me_authenticated(
        self, client: AsyncClient, citizen_user: User, citizen_token: str
    ):
        """Should return current user info for authenticated user."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {citizen_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["phone_number"] == citizen_user.phone_number
        assert data["name"] == citizen_user.name
        assert data["role"] == citizen_user.role.value

    async def test_get_me_unauthenticated(self, client: AsyncClient):
        """Should reject unauthenticated request."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    async def test_get_me_invalid_token(self, client: AsyncClient):
        """Should reject invalid token."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401


class TestRefreshToken:
    """Tests for POST /api/v1/auth/refresh."""

    async def test_refresh_token_missing(self, client: AsyncClient):
        """Should reject missing refresh token."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={},
        )
        assert response.status_code == 422
