"""Authentication schemas."""

import re

from pydantic import BaseModel, Field, field_validator

from app.schemas.base import BaseSchema


# Turkish phone number regex: +90 followed by 10 digits
TURKISH_PHONE_REGEX = re.compile(r"^\+90[0-9]{10}$")


class PhoneNumberMixin(BaseModel):
    """Mixin for phone number validation."""

    phone_number: str = Field(
        ...,
        description="Turkish phone number in format +90XXXXXXXXXX",
        examples=["+905551234567"],
    )

    @field_validator("phone_number")
    @classmethod
    def validate_turkish_phone(cls, v: str) -> str:
        """Validate Turkish phone number format."""
        # Remove spaces and dashes
        cleaned = re.sub(r"[\s\-]", "", v)

        # Check format
        if not TURKISH_PHONE_REGEX.match(cleaned):
            raise ValueError("Invalid Turkish phone number. Format: +90XXXXXXXXXX")
        return cleaned


class RequestOTPRequest(PhoneNumberMixin, BaseSchema):
    """Request to send OTP to phone number (signup only)."""

    pass


class RequestOTPResponse(BaseSchema):
    """Response after requesting OTP."""

    message: str
    expires_in_seconds: int


class VerifyOTPRequest(PhoneNumberMixin, BaseSchema):
    """Request to verify OTP code (signup only)."""

    code: str = Field(
        ...,
        min_length=6,
        max_length=6,
        description="6-digit OTP code",
        examples=["123456"],
    )

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        """Validate OTP code is numeric."""
        if not v.isdigit():
            raise ValueError("OTP code must contain only digits")
        return v


class VerifyOTPResponse(BaseSchema):
    """Response after successful OTP verification (signup)."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str
    requires_registration: bool = True  # New users need to complete registration


class LoginRequest(BaseSchema):
    """Request to login with email and password."""

    email: str = Field(
        ...,
        description="Email address",
        examples=["ahmet@example.com"],
    )
    password: str = Field(
        ...,
        min_length=1,
        description="User password",
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate and normalize email address."""
        from email_validator import EmailNotValidError, validate_email

        try:
            validated = validate_email(v, check_deliverability=False)
            return validated.normalized
        except EmailNotValidError as e:
            raise ValueError(str(e))


class LoginResponse(BaseSchema):
    """Response after successful login."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str


class RegisterRequest(PhoneNumberMixin, BaseSchema):
    """Request to register a new user with email, password, and phone number."""

    full_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="User's full name",
        examples=["Ahmet Yilmaz"],
    )
    email: str = Field(
        ...,
        description="Email address",
        examples=["ahmet@example.com"],
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="User password (min 8 chars, must include letter, number, and special character)",
    )

    @field_validator("full_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate and clean name."""
        cleaned = " ".join(v.split())  # Normalize whitespace
        if len(cleaned) < 2:
            raise ValueError("Name must be at least 2 characters")
        return cleaned

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate and normalize email address."""
        from email_validator import EmailNotValidError, validate_email

        try:
            validated = validate_email(v, check_deliverability=False)
            return validated.normalized
        except EmailNotValidError as e:
            raise ValueError(str(e))

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password meets complexity requirements."""
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("Password must contain at least one letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v


class RegisterResponse(BaseSchema):
    """Response after successful registration."""

    message: str


class StaffLoginRequest(BaseSchema):
    """Request to login as support or manager (staff only)."""

    email: str = Field(
        ...,
        description="Email address",
        examples=["support@example.com"],
    )
    password: str = Field(
        ...,
        min_length=1,
        description="User password",
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate and normalize email address."""
        from email_validator import EmailNotValidError, validate_email

        try:
            validated = validate_email(v, check_deliverability=False)
            return validated.normalized
        except EmailNotValidError as e:
            raise ValueError(str(e))


class RefreshTokenRequest(BaseSchema):
    """Request to refresh access token."""

    refresh_token: str


class TokenResponse(BaseSchema):
    """Response containing new tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class VerifyEmailResponse(BaseSchema):
    """Response after successful email verification."""

    message: str


class ResendVerificationRequest(BaseSchema):
    """Request to resend verification email."""

    email: str = Field(
        ...,
        description="Email address",
        examples=["ahmet@example.com"],
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate and normalize email address."""
        from email_validator import EmailNotValidError, validate_email

        try:
            validated = validate_email(v, check_deliverability=False)
            return validated.normalized
        except EmailNotValidError as e:
            raise ValueError(str(e))


class ResendVerificationResponse(BaseSchema):
    """Response after resending verification email."""

    message: str


class SetPasswordRequest(PhoneNumberMixin, BaseSchema):
    """Request to set password for staff invite flow."""

    token: str = Field(
        ...,
        description="The invite token from the email link",
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password (min 8 chars, must include letter, number, and special character)",
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password meets complexity requirements."""
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("Password must contain at least one letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v


class SetPasswordResponse(BaseSchema):
    """Response after successfully setting password."""

    message: str


class ForgotPasswordRequest(BaseSchema):
    """Request to initiate password reset."""

    email: str = Field(
        ...,
        description="Email address",
        examples=["ahmet@example.com"],
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate and normalize email address."""
        from email_validator import EmailNotValidError, validate_email

        try:
            validated = validate_email(v, check_deliverability=False)
            return validated.normalized
        except EmailNotValidError as e:
            raise ValueError(str(e))


class ForgotPasswordResponse(BaseSchema):
    """Response after password reset request."""

    message: str


class ResetPasswordRequest(BaseSchema):
    """Request to reset password with token."""

    token: str = Field(
        ...,
        description="The password reset token from the email link",
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password (min 8 chars, must include letter, number, and special character)",
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password meets complexity requirements."""
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("Password must contain at least one letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v


class ResetPasswordResponse(BaseSchema):
    """Response after successful password reset."""

    message: str
