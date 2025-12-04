"""Shared API dependencies."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.security import decode_token
from app.database import get_async_session
from app.models.user import User, UserRole

# Security scheme for JWT
security = HTTPBearer()


async def get_db() -> AsyncSession:
    """Get database session dependency."""
    async for session in get_async_session():
        yield session


# Type alias for database session dependency
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: DatabaseSession,
) -> User:
    """Get the current authenticated user from JWT token.

    Args:
        credentials: The HTTP Bearer token credentials.
        db: The database session.

    Returns:
        The authenticated user.

    Raises:
        UnauthorizedException: If the token is invalid or user not found.
    """
    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise UnauthorizedException(detail="Invalid or expired token")

    # Check token type
    if payload.get("type") != "access":
        raise UnauthorizedException(detail="Invalid token type")

    user_id = payload.get("sub")
    if user_id is None:
        raise UnauthorizedException(detail="Invalid token payload")

    # Fetch user from database
    result = await db.execute(
        select(User).where(User.id == UUID(user_id), User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise UnauthorizedException(detail="User not found")

    if not user.is_active:
        raise UnauthorizedException(detail="User account is deactivated")

    return user


# Type alias for current user dependency
CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_active_user(current_user: CurrentUser) -> User:
    """Get current user and verify they are active."""
    if not current_user.is_active:
        raise ForbiddenException(detail="Inactive user")
    return current_user


async def get_current_verified_user(current_user: CurrentUser) -> User:
    """Get current user and verify they are verified."""
    if not current_user.is_verified:
        raise ForbiddenException(detail="User not verified")
    return current_user


# Role-specific dependencies
async def get_support_user(current_user: CurrentUser) -> User:
    """Get current user and verify they are support or manager."""
    if current_user.role not in (UserRole.SUPPORT, UserRole.MANAGER):
        raise ForbiddenException(detail="Support or manager role required")
    return current_user


async def get_manager_user(current_user: CurrentUser) -> User:
    """Get current user and verify they are a manager."""
    if current_user.role != UserRole.MANAGER:
        raise ForbiddenException(detail="Manager role required")
    return current_user


# Type aliases for role-specific dependencies
SupportUser = Annotated[User, Depends(get_support_user)]
ManagerUser = Annotated[User, Depends(get_manager_user)]
