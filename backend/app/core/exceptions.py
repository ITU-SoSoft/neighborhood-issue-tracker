"""Custom exceptions for the application."""

from typing import Any

from fastapi import HTTPException, status


class SoSoftException(HTTPException):
    """Base exception for SoSoft application."""

    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class BadRequestException(SoSoftException):
    """400 Bad Request exception."""

    def __init__(self, detail: str = "Bad request") -> None:
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class UnauthorizedException(SoSoftException):
    """401 Unauthorized exception."""

    def __init__(self, detail: str = "Unauthorized") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenException(SoSoftException):
    """403 Forbidden exception."""

    def __init__(self, detail: str = "Forbidden") -> None:
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class NotFoundException(SoSoftException):
    """404 Not Found exception."""

    def __init__(self, detail: str = "Not found") -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ConflictException(SoSoftException):
    """409 Conflict exception."""

    def __init__(self, detail: str = "Conflict") -> None:
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class UnprocessableEntityException(SoSoftException):
    """422 Unprocessable Entity exception."""

    def __init__(self, detail: str = "Unprocessable entity") -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail
        )


class InternalServerErrorException(SoSoftException):
    """500 Internal Server Error exception."""

    def __init__(self, detail: str = "Internal server error") -> None:
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail
        )


# Specific domain exceptions
class InvalidPhoneNumberException(BadRequestException):
    """Exception for invalid Turkish phone numbers."""

    def __init__(self) -> None:
        super().__init__(detail="Invalid Turkish phone number. Format: +90XXXXXXXXXX")


class OTPExpiredException(BadRequestException):
    """Exception for expired OTP codes."""

    def __init__(self) -> None:
        super().__init__(detail="OTP code has expired")


class OTPInvalidException(BadRequestException):
    """Exception for invalid OTP codes."""

    def __init__(self) -> None:
        super().__init__(detail="Invalid OTP code")


class UserNotFoundException(NotFoundException):
    """Exception when user is not found."""

    def __init__(self) -> None:
        super().__init__(detail="User not found")


class TicketNotFoundException(NotFoundException):
    """Exception when ticket is not found."""

    def __init__(self) -> None:
        super().__init__(detail="Ticket not found")


class CategoryNotFoundException(NotFoundException):
    """Exception when category is not found."""

    def __init__(self) -> None:
        super().__init__(detail="Category not found")


class InvalidStatusTransitionException(BadRequestException):
    """Exception for invalid ticket status transitions."""

    def __init__(self, current: str, target: str) -> None:
        super().__init__(detail=f"Cannot transition from '{current}' to '{target}'")


class TicketAlreadyResolvedException(BadRequestException):
    """Exception when trying to modify a resolved ticket."""

    def __init__(self) -> None:
        super().__init__(detail="Ticket is already resolved")


class FeedbackAlreadyExistsException(ConflictException):
    """Exception when feedback already exists for a ticket."""

    def __init__(self) -> None:
        super().__init__(detail="Feedback already exists for this ticket")


class EscalationAlreadyExistsException(ConflictException):
    """Exception when escalation already exists for a ticket."""

    def __init__(self) -> None:
        super().__init__(detail="Escalation request already exists for this ticket")


class UserNotVerifiedException(UnauthorizedException):
    """Exception when unverified user tries to login."""

    def __init__(self) -> None:
        super().__init__(detail="User is not verified. Please complete signup first.")


class UserAlreadyExistsException(ConflictException):
    """Exception when user already exists during signup."""

    def __init__(self) -> None:
        super().__init__(detail="User already exists. Please use /login instead.")


class InvalidCredentialsException(UnauthorizedException):
    """Exception when email/password combination is invalid."""

    def __init__(self) -> None:
        super().__init__(detail="Invalid email or password")


class EmailAlreadyExistsException(ConflictException):
    """Exception when email is already registered."""

    def __init__(self) -> None:
        super().__init__(detail="An account with this email already exists")


class NotStaffException(ForbiddenException):
    """Exception when non-staff user tries to access staff-only endpoints."""

    def __init__(self) -> None:
        super().__init__(
            detail="Access denied. Staff login is only for support and manager roles."
        )
