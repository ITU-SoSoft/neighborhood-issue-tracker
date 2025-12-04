"""Rate limiting utilities for protecting sensitive endpoints."""

import time
from collections import defaultdict
from dataclasses import dataclass
from functools import wraps
from typing import Callable

from fastapi import HTTPException, Request, status


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    requests: int  # Number of requests allowed
    window_seconds: int  # Time window in seconds


class InMemoryRateLimiter:
    """Simple in-memory rate limiter.

    Note: For production use with multiple workers/instances,
    use Redis-based rate limiting instead.
    """

    def __init__(self):
        # Structure: {key: [(timestamp1, timestamp2, ...)]}
        self._requests: dict[str, list[float]] = defaultdict(list)

    def _cleanup_old_requests(self, key: str, window_seconds: int) -> None:
        """Remove requests outside the current window."""
        current_time = time.time()
        cutoff = current_time - window_seconds
        self._requests[key] = [ts for ts in self._requests[key] if ts > cutoff]

    def is_rate_limited(self, key: str, config: RateLimitConfig) -> tuple[bool, int]:
        """Check if a key is rate limited.

        Args:
            key: Unique identifier (e.g., IP address, phone number)
            config: Rate limit configuration

        Returns:
            Tuple of (is_limited, retry_after_seconds)
        """
        self._cleanup_old_requests(key, config.window_seconds)

        if len(self._requests[key]) >= config.requests:
            # Calculate retry-after
            oldest_request = min(self._requests[key])
            retry_after = int(oldest_request + config.window_seconds - time.time())
            return True, max(retry_after, 1)

        # Record this request
        self._requests[key].append(time.time())
        return False, 0

    def reset(self, key: str) -> None:
        """Reset rate limit for a key."""
        self._requests.pop(key, None)


# Global rate limiter instance
rate_limiter = InMemoryRateLimiter()

# Pre-configured rate limits
OTP_RATE_LIMIT = RateLimitConfig(requests=5, window_seconds=300)  # 5 per 5 minutes
LOGIN_RATE_LIMIT = RateLimitConfig(requests=10, window_seconds=300)  # 10 per 5 minutes
REGISTER_RATE_LIMIT = RateLimitConfig(requests=3, window_seconds=300)  # 3 per 5 minutes


def get_client_ip(request: Request) -> str:
    """Extract client IP from request, handling proxies."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def check_rate_limit(
    request: Request,
    key_suffix: str,
    config: RateLimitConfig,
) -> None:
    """Check rate limit and raise HTTPException if exceeded.

    Args:
        request: FastAPI request object
        key_suffix: Additional key suffix (e.g., phone number)
        config: Rate limit configuration

    Raises:
        HTTPException: If rate limit is exceeded
    """
    client_ip = get_client_ip(request)
    key = f"{client_ip}:{key_suffix}"

    is_limited, retry_after = rate_limiter.is_rate_limited(key, config)
    if is_limited:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many requests. Please try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )
