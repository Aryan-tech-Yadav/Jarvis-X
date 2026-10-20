"""Retry policy, backoff calculation, and circuit breaker for failure recovery."""

from __future__ import annotations

import math
import random
import time
from typing import Dict, Optional


class CircuitBreaker:
    """Circuit breaker to halt repeated failing operations and prevent cascade failures.

    States:
      - CLOSED: Normal operation; requests pass through.
      - OPEN: Failures exceeded threshold; requests fail fast.
      - HALF_OPEN: Cooldown expired; testing recovery with probe requests.
    """

    STATE_CLOSED = "CLOSED"
    STATE_OPEN = "OPEN"
    STATE_HALF_OPEN = "HALF_OPEN"

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: float = 30.0,
        half_open_success_threshold: int = 2,
    ):
        self.failure_threshold = max(1, failure_threshold)
        self.recovery_timeout = max(0.001, float(recovery_timeout))
        self.half_open_success_threshold = max(1, half_open_success_threshold)

        self._consecutive_failures: Dict[str, int] = {}
        self._consecutive_successes: Dict[str, int] = {}
        self._state: Dict[str, str] = {}
        self._opened_at: Dict[str, float] = {}

    def get_state(self, key: str) -> str:
        state = self._state.get(key, self.STATE_CLOSED)
        if state == self.STATE_OPEN:
            opened_time = self._opened_at.get(key, 0.0)
            if time.monotonic() - opened_time >= self.recovery_timeout:
                self._state[key] = self.STATE_HALF_OPEN
                self._consecutive_successes[key] = 0
                return self.STATE_HALF_OPEN
        return state

    def allow_request(self, key: str) -> bool:
        """Return True if execution is permitted, False if circuit is OPEN."""
        state = self.get_state(key)
        return state in (self.STATE_CLOSED, self.STATE_HALF_OPEN)

    def record_success(self, key: str) -> None:
        """Record successful execution, resetting circuit if in HALF_OPEN."""
        state = self.get_state(key)
        if state == self.STATE_HALF_OPEN:
            self._consecutive_successes[key] = self._consecutive_successes.get(key, 0) + 1
            if self._consecutive_successes[key] >= self.half_open_success_threshold:
                self.reset(key)
        elif state == self.STATE_CLOSED:
            self._consecutive_failures[key] = 0

    def record_failure(self, key: str) -> bool:
        """Record a failure. Returns True if the circuit tripped to OPEN."""
        state = self.get_state(key)
        failures = self._consecutive_failures.get(key, 0) + 1
        self._consecutive_failures[key] = failures

        if state == self.STATE_HALF_OPEN or failures >= self.failure_threshold:
            self._state[key] = self.STATE_OPEN
            self._opened_at[key] = time.monotonic()
            return True

        return False

    def reset(self, key: Optional[str] = None) -> None:
        """Reset circuit breaker state for a key or all keys."""
        if key is not None:
            self._state[key] = self.STATE_CLOSED
            self._consecutive_failures[key] = 0
            self._consecutive_successes[key] = 0
            self._opened_at.pop(key, None)
        else:
            self._state.clear()
            self._consecutive_failures.clear()
            self._consecutive_successes.clear()
            self._opened_at.clear()


class RetryPolicy:
    """Configurable retry policy with exponential backoff and circuit breaker support."""

    DEFAULTS = {"research": 5, "validation": 2, "build": 3, "runtime": 4}

    def __init__(
        self,
        limits: Optional[Dict[str, int]] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
    ):
        self.limits = {**self.DEFAULTS, **(limits or {})}
        self.circuit_breaker = circuit_breaker

    def can_retry(self, category: str, attempt: int) -> bool:
        """Check whether another retry attempt is permitted."""
        limit = self.limits.get(category, 1)
        if attempt >= limit:
            return False

        if self.circuit_breaker and not self.circuit_breaker.allow_request(category):
            return False

        return True

    def compute_backoff(
        self,
        attempt: int,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        factor: float = 2.0,
        jitter: bool = True,
    ) -> float:
        """Calculate exponential backoff delay with jitter."""
        if attempt <= 1:
            delay = base_delay
        else:
            delay = min(max_delay, base_delay * (factor ** (attempt - 1)))

        if jitter and delay > 0:
            # Jitter between 50% and 100% of calculated delay
            delay = random.uniform(0.5 * delay, delay)

        return round(delay, 3)
