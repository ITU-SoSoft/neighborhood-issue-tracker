"""Integration tests for core permissions module."""

import pytest

from app.core.permissions import (
    can_approve_escalations,
    can_manage_tickets,
    can_view_analytics,
    is_citizen,
    is_manager,
    is_support,
    is_support_or_manager,
    require_roles,
)
from app.core.exceptions import ForbiddenException
from app.models.user import User, UserRole


class TestRoleCheckFunctions:
    """Tests for role checking helper functions."""

    async def test_is_citizen_returns_true_for_citizen(self, citizen_user: User):
        """is_citizen should return True for citizen users."""
        assert is_citizen(citizen_user) is True

    async def test_is_citizen_returns_false_for_support(self, support_user: User):
        """is_citizen should return False for support users."""
        assert is_citizen(support_user) is False

    async def test_is_citizen_returns_false_for_manager(self, manager_user: User):
        """is_citizen should return False for manager users."""
        assert is_citizen(manager_user) is False

    async def test_is_support_returns_true_for_support(self, support_user: User):
        """is_support should return True for support users."""
        assert is_support(support_user) is True

    async def test_is_support_returns_false_for_citizen(self, citizen_user: User):
        """is_support should return False for citizen users."""
        assert is_support(citizen_user) is False

    async def test_is_support_returns_false_for_manager(self, manager_user: User):
        """is_support should return False for manager users."""
        assert is_support(manager_user) is False

    async def test_is_manager_returns_true_for_manager(self, manager_user: User):
        """is_manager should return True for manager users."""
        assert is_manager(manager_user) is True

    async def test_is_manager_returns_false_for_citizen(self, citizen_user: User):
        """is_manager should return False for citizen users."""
        assert is_manager(citizen_user) is False

    async def test_is_manager_returns_false_for_support(self, support_user: User):
        """is_manager should return False for support users."""
        assert is_manager(support_user) is False


class TestSupportOrManagerCheck:
    """Tests for is_support_or_manager function."""

    async def test_returns_true_for_support(self, support_user: User):
        """is_support_or_manager should return True for support users."""
        assert is_support_or_manager(support_user) is True

    async def test_returns_true_for_manager(self, manager_user: User):
        """is_support_or_manager should return True for manager users."""
        assert is_support_or_manager(manager_user) is True

    async def test_returns_false_for_citizen(self, citizen_user: User):
        """is_support_or_manager should return False for citizen users."""
        assert is_support_or_manager(citizen_user) is False


class TestCanManageTickets:
    """Tests for can_manage_tickets function."""

    async def test_support_can_manage_tickets(self, support_user: User):
        """Support users should be able to manage tickets."""
        assert can_manage_tickets(support_user) is True

    async def test_manager_can_manage_tickets(self, manager_user: User):
        """Managers should be able to manage tickets."""
        assert can_manage_tickets(manager_user) is True

    async def test_citizen_cannot_manage_tickets(self, citizen_user: User):
        """Citizens should not be able to manage tickets."""
        assert can_manage_tickets(citizen_user) is False


class TestCanViewAnalytics:
    """Tests for can_view_analytics function."""

    async def test_manager_can_view_analytics(self, manager_user: User):
        """Managers should be able to view analytics."""
        assert can_view_analytics(manager_user) is True

    async def test_support_cannot_view_analytics(self, support_user: User):
        """Support users should not be able to view analytics."""
        assert can_view_analytics(support_user) is False

    async def test_citizen_cannot_view_analytics(self, citizen_user: User):
        """Citizens should not be able to view analytics."""
        assert can_view_analytics(citizen_user) is False


class TestCanApproveEscalations:
    """Tests for can_approve_escalations function."""

    async def test_manager_can_approve_escalations(self, manager_user: User):
        """Managers should be able to approve escalations."""
        assert can_approve_escalations(manager_user) is True

    async def test_support_cannot_approve_escalations(self, support_user: User):
        """Support users should not be able to approve escalations."""
        assert can_approve_escalations(support_user) is False

    async def test_citizen_cannot_approve_escalations(self, citizen_user: User):
        """Citizens should not be able to approve escalations."""
        assert can_approve_escalations(citizen_user) is False


class TestRequireRolesDecorator:
    """Tests for the require_roles decorator."""

    async def test_allows_user_with_correct_role(self, manager_user: User):
        """Decorator should allow users with the required role."""

        @require_roles(UserRole.MANAGER)
        async def manager_only_func(current_user: User):
            return "success"

        result = await manager_only_func(current_user=manager_user)
        assert result == "success"

    async def test_rejects_user_with_wrong_role(self, citizen_user: User):
        """Decorator should reject users without the required role."""

        @require_roles(UserRole.MANAGER)
        async def manager_only_func(current_user: User):
            return "success"

        with pytest.raises(ForbiddenException) as exc_info:
            await manager_only_func(current_user=citizen_user)
        assert "not allowed" in str(exc_info.value.detail)

    async def test_allows_multiple_roles(self, support_user: User, manager_user: User):
        """Decorator should allow any of the specified roles."""

        @require_roles(UserRole.SUPPORT, UserRole.MANAGER)
        async def staff_only_func(current_user: User):
            return "success"

        # Both support and manager should work
        result_support = await staff_only_func(current_user=support_user)
        assert result_support == "success"

        result_manager = await staff_only_func(current_user=manager_user)
        assert result_manager == "success"

    async def test_rejects_when_user_not_in_allowed_roles(self, citizen_user: User):
        """Decorator should reject users not in the allowed roles list."""

        @require_roles(UserRole.SUPPORT, UserRole.MANAGER)
        async def staff_only_func(current_user: User):
            return "success"

        with pytest.raises(ForbiddenException):
            await staff_only_func(current_user=citizen_user)

    async def test_rejects_when_no_user_provided(self):
        """Decorator should reject when current_user is None."""

        @require_roles(UserRole.MANAGER)
        async def manager_only_func(current_user: User = None):
            return "success"

        with pytest.raises(ForbiddenException) as exc_info:
            await manager_only_func(current_user=None)
        assert "not authenticated" in str(exc_info.value.detail)
