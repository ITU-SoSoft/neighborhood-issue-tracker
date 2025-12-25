"""Authentication API routes."""

import re
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query, Request, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DatabaseSession
from app.config import settings
from app.core.exceptions import (
    EmailAlreadyExistsException,
    EmailAlreadyVerifiedException,
    EmailVerificationTokenExpiredException,
    EmailVerificationTokenInvalidException,
    InvalidCredentialsException,
    NotStaffException,
    OTPExpiredException,
    OTPInvalidException,
    PasswordResetTokenExpiredException,
    PasswordResetTokenInvalidException,
    PhoneNumberMismatchException,
    UserAlreadyExistsException,
    UserNotVerifiedException,
)
from app.core.rate_limit import (
    FORGOT_PASSWORD_RATE_LIMIT,
    LOGIN_RATE_LIMIT,
    OTP_RATE_LIMIT,
    REGISTER_RATE_LIMIT,
    RateLimitConfig,
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
from app.models.user import EmailVerificationToken, OTPCode, User, UserRole
from app.schemas.auth import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RegisterRequest,
    RegisterResponse,
    RequestOTPRequest,
    RequestOTPResponse,
    ResendVerificationRequest,
    ResendVerificationResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    SetPasswordRequest,
    SetPasswordResponse,
    StaffLoginRequest,
    TokenResponse,
    VerifyEmailResponse,
    VerifyOTPRequest,
    VerifyOTPResponse,
)
from app.schemas.user import UserResponse
from app.services.email import email_service
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
    """Register a new citizen user with email, password, and phone number.

    All fields (email, password, phone_number, full_name) are required.
    Email and phone_number must be unique across all users.

    After registration, a verification email is sent. The user must verify
    their email before they can log in.

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

    # Create new user with is_verified=False
    user = User(
        phone_number=request.phone_number,
        name=request.full_name,
        email=request.email,
        password_hash=hash_password(request.password),
        role=UserRole.CITIZEN,
        is_verified=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Generate verification token
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(
        hours=settings.email_verification_expire_hours
    )

    verification_token = EmailVerificationToken(
        user_id=user.id,
        token=token,
        token_type="verification",
        expires_at=expires_at,
    )
    db.add(verification_token)
    await db.commit()

    # Send verification email
    await email_service.send_verification_email(
        to_email=user.email,
        user_name=user.name,
        token=token,
    )

    return RegisterResponse(
        message="Registration successful. Please check your email to verify your account."
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

    # Generate tokens with password_changed_at for invalidation on password reset
    access_token = create_access_token(
        data={"sub": str(user.id)},
        password_changed_at=user.password_changed_at,
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id)},
        password_changed_at=user.password_changed_at,
    )

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

    # Generate tokens with password_changed_at for invalidation on password reset
    access_token = create_access_token(
        data={"sub": str(user.id)},
        password_changed_at=user.password_changed_at,
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id)},
        password_changed_at=user.password_changed_at,
    )

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

    # Generate new tokens with password_changed_at for invalidation on password reset
    access_token = create_access_token(
        data={"sub": str(user.id)},
        password_changed_at=user.password_changed_at,
    )
    new_refresh_token = create_refresh_token(
        data={"sub": str(user.id)},
        password_changed_at=user.password_changed_at,
    )

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
    db: DatabaseSession,
) -> UserResponse:
    """Get the current authenticated user's profile."""
    # Reload user with team relationship to get team name
    result = await db.execute(
        select(User).options(selectinload(User.team)).where(User.id == current_user.id)
    )
    user_with_team = result.scalar_one()

    # Create response with team_name
    user_dict = {
        "id": user_with_team.id,
        "phone_number": user_with_team.phone_number,
        "name": user_with_team.name,
        "email": user_with_team.email,
        "role": user_with_team.role,
        "is_verified": user_with_team.is_verified,
        "is_active": user_with_team.is_active,
        "team_id": user_with_team.team_id,
        "team_name": user_with_team.team.name if user_with_team.team else None,
        "created_at": user_with_team.created_at,
        "updated_at": user_with_team.updated_at,
    }
    return UserResponse.model_validate(user_dict)


@router.get(
    "/verify-email",
    response_model=VerifyEmailResponse,
    status_code=status.HTTP_200_OK,
)
async def verify_email(
    token: str = Query(..., description="Verification token from email"),
    db: DatabaseSession = None,
) -> VerifyEmailResponse:
    """Verify email address using token from verification email.

    This endpoint is called when a citizen clicks the verification link
    in their email. After successful verification, they can log in.
    """
    # Find the token
    result = await db.execute(
        select(EmailVerificationToken).where(
            EmailVerificationToken.token == token,
            EmailVerificationToken.token_type == "verification",
            EmailVerificationToken.is_used == False,  # noqa: E712
        )
    )
    verification_token = result.scalar_one_or_none()

    if verification_token is None:
        raise EmailVerificationTokenInvalidException()

    # Check if expired
    if datetime.now(timezone.utc) > verification_token.expires_at:
        raise EmailVerificationTokenExpiredException()

    # Get the user
    user_result = await db.execute(
        select(User).where(
            User.id == verification_token.user_id,
            User.deleted_at.is_(None),
        )
    )
    user = user_result.scalar_one_or_none()

    if user is None:
        raise EmailVerificationTokenInvalidException()

    if user.is_verified:
        raise EmailAlreadyVerifiedException()

    # Mark token as used and verify user
    verification_token.is_used = True
    user.is_verified = True
    await db.commit()

    return VerifyEmailResponse(
        message="Email verified successfully. You can now log in."
    )


# Rate limit for resend verification: 3 per hour
RESEND_VERIFICATION_RATE_LIMIT = RateLimitConfig(requests=3, window_seconds=3600)


@router.post(
    "/resend-verification",
    response_model=ResendVerificationResponse,
    status_code=status.HTTP_200_OK,
)
async def resend_verification(
    request: ResendVerificationRequest,
    db: DatabaseSession,
    http_request: Request,
) -> ResendVerificationResponse:
    """Resend verification email to a user.

    Rate limited to 3 requests per hour per email.
    Returns a generic success message regardless of whether the email exists
    for security reasons.
    """
    # Check rate limit
    await check_rate_limit(
        http_request,
        f"resend_verification:{request.email}",
        RESEND_VERIFICATION_RATE_LIMIT,
    )

    # Find user by email (don't reveal if email exists)
    result = await db.execute(
        select(User).where(
            User.email == request.email,
            User.deleted_at.is_(None),
        )
    )
    user = result.scalar_one_or_none()

    # Only send if user exists and is not verified
    if user is not None and not user.is_verified:
        # Invalidate old tokens
        old_tokens_result = await db.execute(
            select(EmailVerificationToken).where(
                EmailVerificationToken.user_id == user.id,
                EmailVerificationToken.token_type == "verification",
                EmailVerificationToken.is_used == False,  # noqa: E712
            )
        )
        old_tokens = old_tokens_result.scalars().all()
        for old_token in old_tokens:
            old_token.is_used = True

        # Generate new token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(
            hours=settings.email_verification_expire_hours
        )

        verification_token = EmailVerificationToken(
            user_id=user.id,
            token=token,
            token_type="verification",
            expires_at=expires_at,
        )
        db.add(verification_token)
        await db.commit()

        # Send verification email
        await email_service.send_verification_email(
            to_email=user.email,
            user_name=user.name,
            token=token,
        )

    # Always return success for security (don't reveal if email exists)
    return ResendVerificationResponse(
        message="If an account with this email exists and is not verified, a verification email has been sent."
    )


@router.post(
    "/set-password",
    response_model=SetPasswordResponse,
    status_code=status.HTTP_200_OK,
)
async def set_password(
    request: SetPasswordRequest,
    db: DatabaseSession,
) -> SetPasswordResponse:
    """Set password for staff members invited by manager.

    This endpoint is used when a staff member clicks the invite link
    in their email. They must provide:
    - The token from the email
    - Their phone number (must match what manager entered)
    - Their new password

    After successful password setup, they can log in.
    """
    # Find the token
    result = await db.execute(
        select(EmailVerificationToken).where(
            EmailVerificationToken.token == request.token,
            EmailVerificationToken.token_type == "invite",
            EmailVerificationToken.is_used == False,  # noqa: E712
        )
    )
    verification_token = result.scalar_one_or_none()

    if verification_token is None:
        raise EmailVerificationTokenInvalidException()

    # Check if expired
    if datetime.now(timezone.utc) > verification_token.expires_at:
        raise EmailVerificationTokenExpiredException()

    # Get the user
    user_result = await db.execute(
        select(User).where(
            User.id == verification_token.user_id,
            User.deleted_at.is_(None),
        )
    )
    user = user_result.scalar_one_or_none()

    if user is None:
        raise EmailVerificationTokenInvalidException()

    # Normalize phone numbers for comparison
    def normalize_phone(phone: str) -> str:
        """Normalize phone number for comparison."""
        cleaned = re.sub(r"[\s\-]", "", phone)
        # If starts with 0, replace with +90
        if cleaned.startswith("0"):
            cleaned = "+90" + cleaned[1:]
        # If doesn't start with +, add +90
        if not cleaned.startswith("+"):
            cleaned = "+90" + cleaned
        return cleaned

    # Verify phone number matches
    normalized_request_phone = normalize_phone(request.phone_number)
    normalized_user_phone = normalize_phone(user.phone_number)

    if normalized_request_phone != normalized_user_phone:
        raise PhoneNumberMismatchException()

    # Set password, mark as verified, and update password_changed_at
    verification_token.is_used = True
    user.password_hash = hash_password(request.password)
    user.password_changed_at = datetime.now(timezone.utc)
    user.is_verified = True
    await db.commit()

    return SetPasswordResponse(message="Password set successfully. You can now log in.")


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    status_code=status.HTTP_200_OK,
)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: DatabaseSession,
    http_request: Request,
) -> ForgotPasswordResponse:
    """Request a password reset email.

    Rate limited to 3 requests per hour per email.
    Always returns success for security (don't reveal if email exists).
    """
    # Check rate limit
    await check_rate_limit(
        http_request,
        f"forgot_password:{request.email}",
        FORGOT_PASSWORD_RATE_LIMIT,
    )

    # Find user by email (don't reveal if exists)
    result = await db.execute(
        select(User).where(
            User.email == request.email,
            User.deleted_at.is_(None),
        )
    )
    user = result.scalar_one_or_none()

    # Only send if user exists and is verified
    if user is not None and user.is_verified:
        # Invalidate old password reset tokens
        old_tokens_result = await db.execute(
            select(EmailVerificationToken).where(
                EmailVerificationToken.user_id == user.id,
                EmailVerificationToken.token_type == "password_reset",
                EmailVerificationToken.is_used == False,  # noqa: E712
            )
        )
        old_tokens = old_tokens_result.scalars().all()
        for old_token in old_tokens:
            old_token.is_used = True

        # Generate new token (1 hour expiry)
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        reset_token = EmailVerificationToken(
            user_id=user.id,
            token=token,
            token_type="password_reset",
            expires_at=expires_at,
        )
        db.add(reset_token)
        await db.commit()

        # Send reset email
        await email_service.send_password_reset_email(
            to_email=user.email,
            user_name=user.name,
            token=token,
        )

    # Always return success (security)
    return ForgotPasswordResponse(
        message="If an account with this email exists, a password reset email has been sent."
    )


@router.post(
    "/reset-password",
    response_model=ResetPasswordResponse,
    status_code=status.HTTP_200_OK,
)
async def reset_password(
    request: ResetPasswordRequest,
    db: DatabaseSession,
) -> ResetPasswordResponse:
    """Reset password using token from email.

    The token must be valid and not expired (1 hour).
    After successful reset, all existing sessions are invalidated.
    """
    # Find the token
    result = await db.execute(
        select(EmailVerificationToken).where(
            EmailVerificationToken.token == request.token,
            EmailVerificationToken.token_type == "password_reset",
            EmailVerificationToken.is_used == False,  # noqa: E712
        )
    )
    reset_token = result.scalar_one_or_none()

    if reset_token is None:
        raise PasswordResetTokenInvalidException()

    # Check if expired
    if datetime.now(timezone.utc) > reset_token.expires_at:
        raise PasswordResetTokenExpiredException()

    # Get the user
    user_result = await db.execute(
        select(User).where(
            User.id == reset_token.user_id,
            User.deleted_at.is_(None),
        )
    )
    user = user_result.scalar_one_or_none()

    if user is None:
        raise PasswordResetTokenInvalidException()

    # Update password, mark token as used, and update password_changed_at
    # This invalidates all existing JWT tokens
    reset_token.is_used = True
    user.password_hash = hash_password(request.password)
    user.password_changed_at = datetime.now(timezone.utc)
    await db.commit()

    return ResetPasswordResponse(
        message="Password reset successfully. You can now log in with your new password."
    )
