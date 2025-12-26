"""Integration tests for complete authentication flows."""

from datetime import timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, create_refresh_token
from app.models.user import User, UserRole


# ============================================================================
# Test: End-to-End Authentication Flows
# ============================================================================


class TestAuthenticationFlows:
    """End-to-end authentication flow tests."""

    async def test_login_and_access_protected_endpoint(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Should login and use token to access protected endpoint."""
        from app.core.security import hash_password
        import uuid

        # Create a user
        user = User(
            id=uuid.uuid4(),
            phone_number="+905551234000",
            email="authflow@example.com",
            password_hash=hash_password("TestPassword123!"),
            name="Auth Flow User",
            role=UserRole.CITIZEN,
            is_verified=True,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

        # Login
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "authflow@example.com", "password": "TestPassword123!"},
        )
        assert login_response.status_code == 200
        tokens = login_response.json()
        assert "access_token" in tokens

        # Use access token to get user profile
        me_response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert me_response.status_code == 200
        profile = me_response.json()
        assert profile["email"] == "authflow@example.com"

    async def test_refresh_token_flow(
        self,
        client: AsyncClient,
        citizen_user: User,
    ):
        """Should refresh access token using refresh token."""
        # Create a refresh token
        refresh_token = create_refresh_token(data={"sub": str(citizen_user.id)})

        # Refresh tokens
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

        # New access token should work
        me_response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {data['access_token']}"},
        )
        assert me_response.status_code == 200

    async def test_expired_token_rejected(
        self,
        client: AsyncClient,
        citizen_user: User,
    ):
        """Should reject expired access token."""
        # Create an expired token
        expired_token = create_access_token(
            data={"sub": str(citizen_user.id)},
            expires_delta=timedelta(seconds=-10),  # Already expired
        )

        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert response.status_code == 401

    async def test_invalid_token_rejected(
        self,
        client: AsyncClient,
    ):
        """Should reject malformed token."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code == 401

    async def test_access_token_cannot_be_used_as_refresh(
        self,
        client: AsyncClient,
        citizen_user: User,
    ):
        """Should reject access token used as refresh token."""
        access_token = create_access_token(data={"sub": str(citizen_user.id)})

        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access_token},
        )
        # Should fail - access token has type "access", not "refresh"
        assert response.status_code in [400, 401]


class TestTokenSecurity:
    """Tests for token security edge cases."""

    async def test_deleted_user_token_rejected(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Token for deleted user should be rejected."""
        from app.core.security import hash_password
        from datetime import datetime, timezone
        import uuid

        # Create a deleted user
        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            phone_number="+905551234111",
            email="deleted_auth@example.com",
            password_hash=hash_password("password"),
            name="Deleted User",
            role=UserRole.CITIZEN,
            is_verified=True,
            is_active=True,
            deleted_at=datetime.now(timezone.utc),
        )
        db_session.add(user)
        await db_session.commit()

        # Create token for deleted user
        token = create_access_token(data={"sub": str(user_id)})

        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        # Should fail - user is deleted
        assert response.status_code in [401, 404]

    async def test_inactive_user_token_rejected(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Token for inactive user should be rejected."""
        from app.core.security import hash_password
        import uuid

        # Create an inactive user
        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            phone_number="+905551234222",
            email="inactive_auth@example.com",
            password_hash=hash_password("password"),
            name="Inactive User",
            role=UserRole.CITIZEN,
            is_verified=True,
            is_active=False,  # Inactive
        )
        db_session.add(user)
        await db_session.commit()

        # Create token for inactive user
        token = create_access_token(data={"sub": str(user_id)})

        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        # Should fail - user is inactive
        assert response.status_code in [401, 403]

    async def test_missing_authorization_header(
        self,
        client: AsyncClient,
    ):
        """Should reject request without Authorization header."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    async def test_malformed_authorization_header(
        self,
        client: AsyncClient,
    ):
        """Should reject malformed Authorization header."""
        # Missing "Bearer " prefix
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "invalid_format"},
        )
        assert response.status_code == 401
