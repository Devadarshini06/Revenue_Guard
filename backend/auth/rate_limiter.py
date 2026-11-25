"""
RevenueGuard Authentication Rate Limiter
=========================================
In-memory sliding-window throttle protecting against credential stuffing and brute force.
"""

import time
from typing import Dict, List, Tuple

# Rate limit configuration: 5 failed attempts per 300 seconds (5 minutes)
MAX_FAILED_ATTEMPTS = 5
WINDOW_SECONDS = 300

# Tracks failed attempt timestamps per identifier: Dict[identifier, List[timestamp]]
_attempts: Dict[str, List[float]] = {}


def is_rate_limited(identifier: str) -> Tuple[bool, int]:
    """
    Checks whether the identifier has exceeded the maximum allowed failed attempts
    within the current time window.
    Returns (is_limited, retry_after_seconds).
    """
    now = time.time()
    cutoff = now - WINDOW_SECONDS

    # Clean up stale timestamps
    timestamps = [t for t in _attempts.get(identifier, []) if t > cutoff]
    _attempts[identifier] = timestamps

    if len(timestamps) >= MAX_FAILED_ATTEMPTS:
        oldest_relevant = timestamps[0]
        retry_after = int(WINDOW_SECONDS - (now - oldest_relevant))
        return (True, max(1, retry_after))

    return (False, 0)


def record_failed_attempt(identifier: str) -> None:
    """Records a failed authentication attempt."""
    now = time.time()
    cutoff = now - WINDOW_SECONDS
    timestamps = [t for t in _attempts.get(identifier, []) if t > cutoff]
    timestamps.append(now)
    _attempts[identifier] = timestamps


def reset_attempts(identifier: str) -> None:
    """Clears failed attempts upon successful authentication."""
    if identifier in _attempts:
        del _attempts[identifier]


def clear_all_rate_limits() -> None:
    """Clears all tracked rate limits (useful for test isolation)."""
    _attempts.clear()

