"""Authentication API routes."""

from datetime import datetime, timezone

from fastapi import APIRouter, Request, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DatabaseSession
from app.config import settings
from app.core.exceptions import (
    EmailAlreadyExistsException,
    InvalidCredentialsException,
    NotStaffException,
    OTPExpiredException,
    OTPInvalidException,
    UserAlreadyExistsException,
    UserNotFoundException,
    UserNotVerifiedException,
)
from app.core.rate_limit import (
    LOGIN_RATE_LIMIT,
    OTP_RATE_LIMIT,
    REGISTER_RATE_LIMIT,
    check_rate_limit,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_otp_code,
    get_otp_expiry,
    hash_password,
    verify_password,
)
from app.models.user import OTPCode, User, UserRole
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RegisterRequest,
    RegisterResponse,
    RequestOTPRequest,
    RequestOTPResponse,
    StaffLoginRequest,
    TokenResponse,
    VerifyOTPRequest,
    VerifyOTPResponse,
)
from app.schemas.user import UserResponse
from app.services.sms import sms_service

router = APIRouter()


@router.post(
    "/request-otp",
    response_model=RequestOTPResponse,
    status_code=status.HTTP_200_OK,
)
async def request_otp(
    request: RequestOTPRequest,
    db: DatabaseSession,
    http_request: Request,
) -> RequestOTPResponse:
    """Request an OTP code for signup (new users only).

    This endpoint sends a 6-digit OTP code via SMS to the provided phone number.
    The OTP is valid for 5 minutes. Only works for new users - existing verified
    users should use /login instead.

    Rate limited to 5 requests per 5 minutes per IP/phone combination.
    """
    # Check rate limit
    await check_rate_limit(http_request, f"otp:{request.phone_number}", OTP_RATE_LIMIT)

    # Check if user already exists and is verified
    result = await db.execute(
        select(User).where(
            User.phone_number == request.phone_number,
            User.deleted_at.is_(None),
        )
    )
    existing_user = result.scalar_one_or_none()

    if existing_user is not None and existing_user.is_verified:
        raise UserAlreadyExistsException()

    # Generate OTP code
    code = generate_otp_code(settings.otp_length)
    expires_at = get_otp_expiry()

    # Save OTP to database
    otp = OTPCode(
        phone_number=request.phone_number,
        code=code,
        expires_at=expires_at,
    )
    db.add(otp)
    await db.commit()

    # Send SMS
    await sms_service.send_otp(request.phone_number, code)

    return RequestOTPResponse(
        message="OTP code sent successfully",
        expires_in_seconds=settings.otp_expire_minutes * 60,
    )


@router.post(
    "/verify-otp",
    response_model=VerifyOTPResponse,
    status_code=status.HTTP_200_OK,
)
async def verify_otp(
    request: VerifyOTPRequest,
    db: DatabaseSession,
) -> VerifyOTPResponse:
    """Verify an OTP code and return JWT tokens.

    If the user doesn't exist, a new user is created with is_verified=False.
    The client should then call /register to complete registration.
    """
    # Find the most recent unused OTP for this phone number
    result = await db.execute(
        select(OTPCode)
        .where(
            OTPCode.phone_number == request.phone_number,
            OTPCode.code == request.code,
            OTPCode.is_used == False,  # noqa: E712
        )
        .order_by(OTPCode.created_at.desc())
        .limit(1)
    )
    otp = result.scalar_one_or_none()

    if otp is None:
        raise OTPInvalidException()

    # Check if expired
    if datetime.now(timezone.utc) > otp.expires_at:
        raise OTPExpiredException()

    # Mark OTP as used
    otp.is_used = True
    await db.commit()

    # Find or create user
    result = await db.execute(
        select(User).where(
            User.phone_number == request.phone_number,
            User.deleted_at.is_(None),
        )
    )
    user = result.scalar_one_or_none()

    is_new_user = user is None
    if is_new_user:
        # Create new user
        user = User(
            phone_number=request.phone_number,
            name="New User",
            role=UserRole.CITIZEN,
            is_verified=False,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # Generate tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return VerifyOTPResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        requires_registration=is_new_user or not user.is_verified,
        user_id=str(user.id),
    )


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    request: RegisterRequest,
    db: DatabaseSession,
    http_request: Request,
) -> RegisterResponse:
    """Register a new user with email, password, and phone number.

    All fields (email, password, phone_number, full_name) are required.
    Email and phone_number must be unique across all users.

    Rate limited to 3 requests per 5 minutes per IP/phone combination.
    """
    # Check rate limit
    await check_rate_limit(
        http_request, f"register:{request.phone_number}", REGISTER_RATE_LIMIT
    )

    # Check if phone number is already taken
    result = await db.execute(
        select(User).where(
            User.phone_number == request.phone_number,
            User.deleted_at.is_(None),
        )
    )
    existing_phone_user = result.scalar_one_or_none()
    if existing_phone_user is not None:
        raise UserAlreadyExistsException()

    # Check if email is already taken
    email_result = await db.execute(
        select(User).where(
            User.email == request.email,
            User.deleted_at.is_(None),
        )
    )
    existing_email_user = email_result.scalar_one_or_none()
    if existing_email_user is not None:
        raise EmailAlreadyExistsException()

    # Create new user
    user = User(
        phone_number=request.phone_number,
        name=request.full_name,
        email=request.email,
        password_hash=hash_password(request.password),
        role=UserRole.CITIZEN,
        is_verified=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Generate tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return RegisterResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=str(user.id),
    )


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
)
async def login(
    request: LoginRequest,
    db: DatabaseSession,
    http_request: Request,
) -> LoginResponse:
    """Login with email and password.

    This endpoint allows verified users to login with their email and password.
    New users should use /request-otp, /verify-otp, and /register to sign up first.

    Rate limited to 10 requests per 5 minutes per IP/email combination.
    """
    # Check rate limit
    await check_rate_limit(http_request, f"login:{request.email}", LOGIN_RATE_LIMIT)

    # Find user by email
    result = await db.execute(
        select(User).where(
            User.email == request.email,
            User.deleted_at.is_(None),
        )
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise InvalidCredentialsException()

    if not user.is_verified:
        raise UserNotVerifiedException()

    # Verify password
    if not verify_password(request.password, user.password_hash):
        raise InvalidCredentialsException()

    # Generate tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=str(user.id),
    )


@router.post(
    "/staff/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
)
async def staff_login(
    request: StaffLoginRequest,
    db: DatabaseSession,
    http_request: Request,
) -> LoginResponse:
    """Login for support and manager roles only.

    This endpoint allows only staff members (support and manager roles) to login.
    Citizens should use the regular /login endpoint.

    Rate limited to 10 requests per 5 minutes per IP/email combination.
    """
    # Check rate limit
    await check_rate_limit(
        http_request, f"staff_login:{request.email}", LOGIN_RATE_LIMIT
    )

    # Find user by email
    result = await db.execute(
        select(User).where(
            User.email == request.email,
            User.deleted_at.is_(None),
        )
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise InvalidCredentialsException()

    if not user.is_verified:
        raise UserNotVerifiedException()

    # Check if user is staff (support or manager)
    if user.role not in (UserRole.SUPPORT, UserRole.MANAGER):
        raise NotStaffException()

    # Verify password
    if not verify_password(request.password, user.password_hash):
        raise InvalidCredentialsException()

    # Generate tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=str(user.id),
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
async def refresh_token(
    request: RefreshTokenRequest,
    db: DatabaseSession,
) -> TokenResponse:
    """Refresh access token using a refresh token."""
    payload = decode_token(request.refresh_token)

    if payload is None or payload.get("type") != "refresh":
        raise OTPInvalidException()  # Reusing for simplicity

    user_id = payload.get("sub")
    if user_id is None:
        raise OTPInvalidException()

    # Verify user exists
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise OTPInvalidException()

    # Generate new tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
    )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
async def get_current_user_info(
    current_user: CurrentUser,
) -> UserResponse:
    """Get the current authenticated user's profile."""
    return UserResponse.model_validate(current_user)
