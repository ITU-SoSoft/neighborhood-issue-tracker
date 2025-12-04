"""Role-based access control decorators and utilities."""

from functools import wraps
from typing import Callable

from fastapi import Depends

from app.core.exceptions import ForbiddenException
from app.models.user import User, UserRole


def require_roles(*allowed_roles: UserRole) -> Callable:
    """Decorator to require specific roles for an endpoint.

    Args:
        allowed_roles: The roles that are allowed to access the endpoint.

    Returns:
        A decorator function.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # The current_user should be injected via Depends
            current_user: User | None = kwargs.get("current_user")
            if current_user is None:
                raise ForbiddenException(detail="User not authenticated")

            if current_user.role not in allowed_roles:
                raise ForbiddenException(
                    detail=f"Role '{current_user.role.value}' is not allowed to perform this action"
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def is_citizen(user: User) -> bool:
    """Check if user is a citizen."""
    return user.role == UserRole.CITIZEN


def is_support(user: User) -> bool:
    """Check if user is a support member."""
    return user.role == UserRole.SUPPORT


def is_manager(user: User) -> bool:
    """Check if user is a manager."""
    return user.role == UserRole.MANAGER


def is_support_or_manager(user: User) -> bool:
    """Check if user is a support member or manager."""
    return user.role in (UserRole.SUPPORT, UserRole.MANAGER)


def can_manage_tickets(user: User) -> bool:
    """Check if user can manage tickets (support or manager)."""
    return is_support_or_manager(user)


def can_view_analytics(user: User) -> bool:
    """Check if user can view analytics (manager only)."""
    return is_manager(user)


def can_approve_escalations(user: User) -> bool:
    """Check if user can approve escalations (manager only)."""
    return is_manager(user)
