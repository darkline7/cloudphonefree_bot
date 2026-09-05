"""Rate limiting and cooldown middleware."""

import time
from typing import Dict, Optional


class RateLimiter:
    """In-memory sliding window rate limiter per user."""

    def __init__(self, cooldown_seconds: int = 10) -> None:
        self.cooldown_seconds = cooldown_seconds
        self._last_actions: Dict[int, float] = {}

    def is_rate_limited(self, user_id: int) -> bool:
        """Check if user is currently in cooldown period."""
        now = time.time()
        last_time = self._last_actions.get(user_id, 0.0)
        if now - last_time < self.cooldown_seconds:
            return True
        self._last_actions[user_id] = now
        return False

    def remaining_cooldown(self, user_id: int) -> int:
        """Calculate remaining cooldown in seconds."""
        now = time.time()
        last_time = self._last_actions.get(user_id, 0.0)
        remaining = self.cooldown_seconds - (now - last_time)
        return max(0, int(remaining))

    def reset(self, user_id: Optional[int] = None) -> None:
        """Reset rate limiter for specific user or all users."""
        if user_id:
            self._last_actions.pop(user_id, None)
        else:
            self._last_actions.clear()
