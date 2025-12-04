"""Tests for permission utilities."""

import pytest
from unittest.mock import MagicMock

from app.core.permissions import (
    is_citizen,
    is_support,
    is_manager,
    is_support_or_manager,
    can_manage_tickets,
    can_view_analytics,
    can_approve_escalations,
)
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
