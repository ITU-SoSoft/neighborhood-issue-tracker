"""Tests for permission utilities."""

import pytest
from unittest.mock import MagicMock

from app.core.permissions import (
    require_roles,
    is_citizen,
    is_support,
    is_manager,
    is_support_or_manager,
    can_manage_tickets,
    can_view_analytics,
    can_approve_escalations,
)
from app.core.exceptions import ForbiddenException
from app.models import User, UserRole


class TestRoleChecks:
    """Tests for role checking functions."""

    def test_is_citizen(self):
        """Should correctly identify citizen role."""
        user = MagicMock(spec=User)
        user.role = UserRole.CITIZEN
        assert is_citizen(user) is True

        user.role = UserRole.SUPPORT
        assert is_citizen(user) is False

        user.role = UserRole.MANAGER
        assert is_citizen(user) is False

    def test_is_support(self):
        """Should correctly identify support role."""
        user = MagicMock(spec=User)
        user.role = UserRole.SUPPORT
        assert is_support(user) is True

        user.role = UserRole.CITIZEN
        assert is_support(user) is False

        user.role = UserRole.MANAGER
        assert is_support(user) is False

    def test_is_manager(self):
        """Should correctly identify manager role."""
        user = MagicMock(spec=User)
        user.role = UserRole.MANAGER
        assert is_manager(user) is True

        user.role = UserRole.CITIZEN
        assert is_manager(user) is False

        user.role = UserRole.SUPPORT
        assert is_manager(user) is False

    def test_is_support_or_manager(self):
        """Should correctly identify support or manager role."""
        user = MagicMock(spec=User)

        user.role = UserRole.SUPPORT
        assert is_support_or_manager(user) is True

        user.role = UserRole.MANAGER
        assert is_support_or_manager(user) is True

        user.role = UserRole.CITIZEN
        assert is_support_or_manager(user) is False


class TestPermissionChecks:
    """Tests for permission checking functions."""

    def test_can_manage_tickets(self):
        """Support and managers can manage tickets."""
        user = MagicMock(spec=User)

        user.role = UserRole.SUPPORT
        assert can_manage_tickets(user) is True

        user.role = UserRole.MANAGER
        assert can_manage_tickets(user) is True

        user.role = UserRole.CITIZEN
        assert can_manage_tickets(user) is False

    def test_can_view_analytics(self):
        """Only managers can view analytics."""
        user = MagicMock(spec=User)

        user.role = UserRole.MANAGER
        assert can_view_analytics(user) is True

        user.role = UserRole.SUPPORT
        assert can_view_analytics(user) is False

        user.role = UserRole.CITIZEN
        assert can_view_analytics(user) is False

    def test_can_approve_escalations(self):
        """Only managers can approve escalations."""
        user = MagicMock(spec=User)

        user.role = UserRole.MANAGER
        assert can_approve_escalations(user) is True

        user.role = UserRole.SUPPORT
        assert can_approve_escalations(user) is False

        user.role = UserRole.CITIZEN
        assert can_approve_escalations(user) is False


class TestRequireRolesDecorator:
    """Tests for the require_roles decorator."""

    async def test_require_roles_allows_valid_role(self):
        """Decorator should allow user with valid role."""
        user = MagicMock(spec=User)
        user.role = UserRole.MANAGER

        @require_roles(UserRole.MANAGER, UserRole.SUPPORT)
        async def protected_endpoint(current_user: User):
            return "success"

        result = await protected_endpoint(current_user=user)
        assert result == "success"

    async def test_require_roles_denies_invalid_role(self):
        """Decorator should deny user with invalid role."""
        user = MagicMock(spec=User)
        user.role = UserRole.CITIZEN

        @require_roles(UserRole.MANAGER, UserRole.SUPPORT)
        async def protected_endpoint(current_user: User):
            return "success"

        with pytest.raises(ForbiddenException) as exc_info:
            await protected_endpoint(current_user=user)

        assert "not allowed" in str(exc_info.value.detail)

    async def test_require_roles_denies_unauthenticated_user(self):
        """Decorator should deny when current_user is None."""

        @require_roles(UserRole.MANAGER)
        async def protected_endpoint(current_user=None):
            return "success"

        with pytest.raises(ForbiddenException) as exc_info:
            await protected_endpoint(current_user=None)

        assert "not authenticated" in str(exc_info.value.detail)

    async def test_require_roles_allows_single_role(self):
        """Decorator should work with a single role requirement."""
        user = MagicMock(spec=User)
        user.role = UserRole.SUPPORT

        @require_roles(UserRole.SUPPORT)
        async def support_only_endpoint(current_user: User):
            return "support access"

        result = await support_only_endpoint(current_user=user)
        assert result == "support access"

    async def test_require_roles_preserves_function_return(self):
        """Decorator should preserve the wrapped function's return value."""
        user = MagicMock(spec=User)
        user.role = UserRole.MANAGER

        @require_roles(UserRole.MANAGER)
        async def return_data_endpoint(current_user: User):
            return {"data": "test", "user_role": current_user.role}

        result = await return_data_endpoint(current_user=user)
        assert result == {"data": "test", "user_role": UserRole.MANAGER}
