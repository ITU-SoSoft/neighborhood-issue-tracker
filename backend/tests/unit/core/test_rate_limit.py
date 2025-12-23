"""Tests for rate limiting utilities."""

import time
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.core.rate_limit import (
    RateLimitConfig,
    InMemoryRateLimiter,
    get_client_ip,
    check_rate_limit,
    rate_limiter,
)


class TestRateLimitConfig:
    """Tests for RateLimitConfig dataclass."""

    def test_config_creation(self):
        """Should create config with correct values."""
        config = RateLimitConfig(requests=5, window_seconds=300)
        assert config.requests == 5
        assert config.window_seconds == 300


class TestInMemoryRateLimiter:
    """Tests for InMemoryRateLimiter class."""

    def test_first_request_not_limited(self):
        """First request should not be rate limited."""
        limiter = InMemoryRateLimiter()
        config = RateLimitConfig(requests=5, window_seconds=60)

        is_limited, retry_after = limiter.is_rate_limited("test_key", config)

        assert is_limited is False
        assert retry_after == 0

    def test_under_limit_not_limited(self):
        """Requests under the limit should not be rate limited."""
        limiter = InMemoryRateLimiter()
        config = RateLimitConfig(requests=5, window_seconds=60)

        # Make 4 requests (under limit of 5)
        for _ in range(4):
            is_limited, _ = limiter.is_rate_limited("test_key", config)
            assert is_limited is False

    def test_at_limit_becomes_limited(self):
        """Requests at the limit should become rate limited."""
        limiter = InMemoryRateLimiter()
        config = RateLimitConfig(requests=3, window_seconds=60)

        # Make 3 requests (at limit)
        for _ in range(3):
            limiter.is_rate_limited("test_key", config)

        # 4th request should be limited
        is_limited, retry_after = limiter.is_rate_limited("test_key", config)

        assert is_limited is True
        assert retry_after >= 1

    def test_different_keys_independent(self):
        """Different keys should have independent rate limits."""
        limiter = InMemoryRateLimiter()
        config = RateLimitConfig(requests=2, window_seconds=60)

        # Exhaust limit for key1
        limiter.is_rate_limited("key1", config)
        limiter.is_rate_limited("key1", config)
        is_limited_key1, _ = limiter.is_rate_limited("key1", config)

        # key2 should still be available
        is_limited_key2, _ = limiter.is_rate_limited("key2", config)

        assert is_limited_key1 is True
        assert is_limited_key2 is False

    def test_reset_clears_limit(self):
        """Reset should clear rate limit for a key."""
        limiter = InMemoryRateLimiter()
        config = RateLimitConfig(requests=2, window_seconds=60)

        # Exhaust limit
        limiter.is_rate_limited("test_key", config)
        limiter.is_rate_limited("test_key", config)

        # Reset
        limiter.reset("test_key")

        # Should no longer be limited
        is_limited, _ = limiter.is_rate_limited("test_key", config)
        assert is_limited is False

    def test_reset_nonexistent_key_no_error(self):
        """Reset on nonexistent key should not raise error."""
        limiter = InMemoryRateLimiter()
        # Should not raise
        limiter.reset("nonexistent_key")

    def test_cleanup_old_requests(self):
        """Old requests outside window should be cleaned up."""
        limiter = InMemoryRateLimiter()
        config = RateLimitConfig(requests=2, window_seconds=1)

        # Make requests
        limiter.is_rate_limited("test_key", config)
        limiter.is_rate_limited("test_key", config)

        # Wait for window to expire
        time.sleep(1.1)

        # Should no longer be limited (old requests cleaned up)
        is_limited, _ = limiter.is_rate_limited("test_key", config)
        assert is_limited is False


class TestGetClientIP:
    """Tests for get_client_ip function."""

    def test_get_ip_from_x_forwarded_for(self):
        """Should extract IP from X-Forwarded-For header."""
        request = MagicMock()
        request.headers.get.return_value = "192.168.1.1, 10.0.0.1"

        ip = get_client_ip(request)

        assert ip == "192.168.1.1"

    def test_get_ip_from_client_host(self):
        """Should fall back to client.host when no X-Forwarded-For."""
        request = MagicMock()
        request.headers.get.return_value = None
        request.client.host = "127.0.0.1"

        ip = get_client_ip(request)

        assert ip == "127.0.0.1"

    def test_get_ip_no_client(self):
        """Should return 'unknown' when no client info available."""
        request = MagicMock()
        request.headers.get.return_value = None
        request.client = None

        ip = get_client_ip(request)

        assert ip == "unknown"

    def test_get_ip_strips_whitespace(self):
        """Should strip whitespace from forwarded IP."""
        request = MagicMock()
        request.headers.get.return_value = "  192.168.1.1  , 10.0.0.1"

        ip = get_client_ip(request)

        assert ip == "192.168.1.1"


class TestCheckRateLimit:
    """Tests for check_rate_limit async function."""

    async def test_check_rate_limit_passes_under_limit(self):
        """Should not raise when under rate limit."""
        request = MagicMock()
        request.headers.get.return_value = None
        request.client.host = "192.168.1.100"

        config = RateLimitConfig(requests=10, window_seconds=60)

        # Should not raise
        await check_rate_limit(request, "test_action", config)

    async def test_check_rate_limit_raises_when_limited(self):
        """Should raise HTTPException when rate limited."""
        request = MagicMock()
        request.headers.get.return_value = None
        request.client.host = "192.168.1.200"

        config = RateLimitConfig(requests=1, window_seconds=60)

        # First request OK
        await check_rate_limit(request, "test_action_limited", config)

        # Second request should be limited
        with pytest.raises(HTTPException) as exc_info:
            await check_rate_limit(request, "test_action_limited", config)

        assert exc_info.value.status_code == 429
        assert "Too many requests" in exc_info.value.detail
        assert "Retry-After" in exc_info.value.headers

    async def test_check_rate_limit_uses_key_suffix(self):
        """Should use key suffix to differentiate rate limits."""
        request = MagicMock()
        request.headers.get.return_value = None
        request.client.host = "192.168.1.300"

        config = RateLimitConfig(requests=1, window_seconds=60)

        # First action exhausts limit
        await check_rate_limit(request, "action_a", config)

        # Different action should still work
        await check_rate_limit(request, "action_b", config)

        # Original action should be limited
        with pytest.raises(HTTPException):
            await check_rate_limit(request, "action_a", config)
