"""Tests for authentication endpoints."""

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
        # Could be 422 (validation) or 400 (bad request)
        assert response.status_code in [400, 422]

    async def test_request_otp_non_turkish_phone(self, client: AsyncClient):
        """Should reject non-Turkish phone numbers."""
        response = await client.post(
            "/api/v1/auth/request-otp",
            json={"phone_number": "+12025551234"},  # US number
        )
        # Could be 422 (validation) or 400 (bad request)
        assert response.status_code in [400, 422]


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

    async def test_login_verified_user(self, client: AsyncClient, db_session):
        """Should login verified user successfully with email and password."""
        from app.models.user import User, UserRole
        from app.core.security import hash_password

        # Create a user with email and password
        user = User(
            phone_number="+905551112233",
            email="testlogin@example.com",
            password_hash=hash_password("testpassword123"),
            name="Test Login User",
            role=UserRole.CITIZEN,
            is_verified=True,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "testlogin@example.com", "password": "testpassword123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "user_id" in data

    async def test_login_unverified_user(self, client: AsyncClient, db_session):
        """Should reject login for unverified user."""
        from app.models.user import User, UserRole
        from app.core.security import hash_password

        # Create an unverified user with email and password
        user = User(
            phone_number="+905552223344",
            email="unverified@example.com",
            password_hash=hash_password("testpassword123"),
            name="Unverified User",
            role=UserRole.CITIZEN,
            is_verified=False,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "unverified@example.com", "password": "testpassword123"},
        )
        # 401 Unauthorized - user must complete verification first
        assert response.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Should reject login for nonexistent user."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@example.com", "password": "anypassword"},
        )
        # 401 Unauthorized - invalid credentials
        assert response.status_code == 401


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

    async def test_refresh_token_valid(
        self, client: AsyncClient, citizen_user, db_session
    ):
        """Should refresh tokens for valid refresh token."""
        from app.core.security import create_refresh_token

        refresh_token = create_refresh_token(data={"sub": str(citizen_user.id)})

        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_refresh_token_invalid(self, client: AsyncClient):
        """Should reject invalid refresh token."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid_token"},
        )
        # Should return 400 or 401 for invalid token
        assert response.status_code in [400, 401]

    async def test_refresh_token_wrong_type(self, client: AsyncClient, citizen_user):
        """Should reject access token used as refresh token."""
        from app.core.security import create_access_token

        # Try to use access token as refresh token
        access_token = create_access_token(data={"sub": str(citizen_user.id)})

        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access_token},
        )
        # Should reject because it's not a refresh token type
        assert response.status_code in [400, 401]


class TestRegister:
    """Tests for POST /api/v1/auth/register."""

    async def test_register_new_user(self, client: AsyncClient):
        """Should register a new user successfully and return verification message."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "phone_number": "+905559991122",
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "full_name": "New Test User",
            },
        )
        assert response.status_code == 201
        data = response.json()
        # New behavior: returns message instead of tokens (email verification required)
        assert "message" in data
        assert (
            "verification" in data["message"].lower()
            or "email" in data["message"].lower()
        )

    async def test_register_duplicate_email(self, client: AsyncClient, db_session):
        """Should reject registration with duplicate email."""
        from app.models.user import User, UserRole
        from app.core.security import hash_password

        # Create existing user
        existing_user = User(
            phone_number="+905558887766",
            email="existing@example.com",
            password_hash=hash_password("password123"),
            name="Existing User",
            role=UserRole.CITIZEN,
            is_verified=True,
            is_active=True,
        )
        db_session.add(existing_user)
        await db_session.commit()

        # Try to register with same email
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "phone_number": "+905551112233",
                "email": "existing@example.com",
                "password": "SecurePass123!",
                "full_name": "Another User",
            },
        )
        assert response.status_code == 409

    async def test_register_duplicate_phone(self, client: AsyncClient, db_session):
        """Should reject registration with duplicate phone number."""
        from app.models.user import User, UserRole
        from app.core.security import hash_password

        # Create existing user
        existing_user = User(
            phone_number="+905551234567",
            email="phone_existing@example.com",
            password_hash=hash_password("password123"),
            name="Existing User",
            role=UserRole.CITIZEN,
            is_verified=True,
            is_active=True,
        )
        db_session.add(existing_user)
        await db_session.commit()

        # Try to register with same phone
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "phone_number": "+905551234567",
                "email": "newphone@example.com",
                "password": "SecurePass123!",
                "full_name": "Another User",
            },
        )
        assert response.status_code == 409


class TestStaffLogin:
    """Tests for POST /api/v1/auth/staff/login."""

    async def test_staff_login_support(self, client: AsyncClient, db_session):
        """Support user should be able to login via staff endpoint."""
        from app.models.user import User, UserRole
        from app.core.security import hash_password

        # Create support user
        support = User(
            phone_number="+905553334455",
            email="support_staff@example.com",
            password_hash=hash_password("staffpass123"),
            name="Support Staff",
            role=UserRole.SUPPORT,
            is_verified=True,
            is_active=True,
        )
        db_session.add(support)
        await db_session.commit()

        response = await client.post(
            "/api/v1/auth/staff/login",
            json={"email": "support_staff@example.com", "password": "staffpass123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_staff_login_manager(self, client: AsyncClient, db_session):
        """Manager should be able to login via staff endpoint."""
        from app.models.user import User, UserRole
        from app.core.security import hash_password

        # Create manager user
        manager = User(
            phone_number="+905554445566",
            email="manager_staff@example.com",
            password_hash=hash_password("managerpass123"),
            name="Manager Staff",
            role=UserRole.MANAGER,
            is_verified=True,
            is_active=True,
        )
        db_session.add(manager)
        await db_session.commit()

        response = await client.post(
            "/api/v1/auth/staff/login",
            json={"email": "manager_staff@example.com", "password": "managerpass123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    async def test_staff_login_citizen_rejected(self, client: AsyncClient, db_session):
        """Citizen should NOT be able to login via staff endpoint."""
        from app.models.user import User, UserRole
        from app.core.security import hash_password

        # Create citizen user
        citizen = User(
            phone_number="+905555556677",
            email="citizen_notstaff@example.com",
            password_hash=hash_password("citizenpass123"),
            name="Regular Citizen",
            role=UserRole.CITIZEN,
            is_verified=True,
            is_active=True,
        )
        db_session.add(citizen)
        await db_session.commit()

        response = await client.post(
            "/api/v1/auth/staff/login",
            json={
                "email": "citizen_notstaff@example.com",
                "password": "citizenpass123",
            },
        )
        # Should be rejected - citizens are not staff
        assert response.status_code == 403

    async def test_staff_login_wrong_password(self, client: AsyncClient, db_session):
        """Should reject staff login with wrong password."""
        from app.models.user import User, UserRole
        from app.core.security import hash_password

        support = User(
            phone_number="+905556667788",
            email="wrongpass_staff@example.com",
            password_hash=hash_password("correctpass123"),
            name="Staff User",
            role=UserRole.SUPPORT,
            is_verified=True,
            is_active=True,
        )
        db_session.add(support)
        await db_session.commit()

        response = await client.post(
            "/api/v1/auth/staff/login",
            json={"email": "wrongpass_staff@example.com", "password": "wrongpassword"},
        )
        assert response.status_code == 401

    async def test_staff_login_unverified_rejected(
        self, client: AsyncClient, db_session
    ):
        """Should reject staff login for unverified user."""
        from app.models.user import User, UserRole
        from app.core.security import hash_password

        support = User(
            phone_number="+905557778899",
            email="unverified_staff@example.com",
            password_hash=hash_password("staffpass123"),
            name="Unverified Staff",
            role=UserRole.SUPPORT,
            is_verified=False,
            is_active=True,
        )
        db_session.add(support)
        await db_session.commit()

        response = await client.post(
            "/api/v1/auth/staff/login",
            json={"email": "unverified_staff@example.com", "password": "staffpass123"},
        )
        assert response.status_code == 401


class TestOTPVerification:
    """Tests for OTP verification flow."""

    async def test_verify_valid_otp_existing_user(
        self, client: AsyncClient, db_session
    ):
        """Should verify OTP and return tokens for existing user."""
        from app.models.user import User, OTPCode, UserRole
        from datetime import datetime, timezone, timedelta

        # Create existing user
        user = User(
            phone_number="+905559990011",
            email="otp_test@example.com",
            password_hash="dummy_hash",
            name="OTP Test User",
            role=UserRole.CITIZEN,
            is_verified=True,
            is_active=True,
        )
        db_session.add(user)

        # Create valid OTP
        otp = OTPCode(
            phone_number="+905559990011",
            code="123456",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
            is_used=False,
        )
        db_session.add(otp)
        await db_session.commit()

        response = await client.post(
            "/api/v1/auth/verify-otp",
            json={"phone_number": "+905559990011", "code": "123456"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_verify_expired_otp(self, client: AsyncClient, db_session):
        """Should reject expired OTP."""
        from app.models.user import OTPCode
        from datetime import datetime, timezone, timedelta

        # Create expired OTP
        otp = OTPCode(
            phone_number="+905559990022",
            code="654321",
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=10),  # Expired
            is_used=False,
        )
        db_session.add(otp)
        await db_session.commit()

        response = await client.post(
            "/api/v1/auth/verify-otp",
            json={"phone_number": "+905559990022", "code": "654321"},
        )
        # Should be rejected because OTP is expired
        assert response.status_code == 400

    async def test_request_otp_existing_verified_user(
        self, client: AsyncClient, citizen_user
    ):
        """Should reject OTP request for already verified user."""
        response = await client.post(
            "/api/v1/auth/request-otp",
            json={"phone_number": citizen_user.phone_number},
        )
        # Should reject because user is already verified
        assert response.status_code == 409


class TestLoginWrongPassword:
    """Additional login tests."""

    async def test_login_wrong_password(self, client: AsyncClient, db_session):
        """Should reject login with wrong password."""
        from app.models.user import User, UserRole
        from app.core.security import hash_password

        user = User(
            phone_number="+905558889900",
            email="wrongpass@example.com",
            password_hash=hash_password("correctpassword"),
            name="Wrong Pass User",
            role=UserRole.CITIZEN,
            is_verified=True,
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "wrongpass@example.com", "password": "wrongpassword"},
        )
        assert response.status_code == 401
