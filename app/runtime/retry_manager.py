"""Retry manager for autonomous failure recovery.

When a task fails, instead of stopping:
  retry -> repair -> retest -> continue

Rules:
  - max retries
  - timeout per attempt
  - escalation threshold
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class RetryPolicy:
    """Retry policy for a task."""

    max_retries: int = 3
    timeout_seconds: float = 60.0
    backoff_factor: float = 2.0
    initial_delay_seconds: float = 1.0
    escalate_after: int = 2


@dataclass
class RetryResult:
    """Result of a retry attempt."""

    success: bool
    attempts: int
    total_time: float
    last_error: str = ""
    escalated: bool = False
    output: Any = None


class RetryManager:
    """Manage retries, repair loops, and escalation."""

    def __init__(self, policy: Optional[RetryPolicy] = None):
        self.policy = policy or RetryPolicy()
        self._history: List[Dict[str, Any]] = []

    def execute_with_retry(self, task_name: str, handler: Callable[[], Any],
                           repair_handler: Optional[Callable[[Any], Any]] = None) -> RetryResult:
        """Execute a task with retry and optional repair.

        Flow:
          1. attempt
          2. if fail -> repair
          3. retry
          4. repeat until success or max_retries
          5. escalate if threshold reached
        """
        start = time.perf_counter()
        attempts = 0
        last_error = ""
        output = None
        escalated = False

        while attempts <= self.policy.max_retries:
            attempts += 1
            try:
                output = handler()
                return RetryResult(
                    success=True,
                    attempts=attempts,
                    total_time=time.perf_counter() - start,
                    output=output,
                )
            except Exception as exc:
                last_error = str(exc)
                if repair_handler and attempts <= self.policy.max_retries:
                    try:
                        repair_handler(exc)
                    except Exception:
                        pass
                if attempts >= self.policy.escalate_after and attempts >= self.policy.max_retries:
                    escalated = True
                    break

        return RetryResult(
            success=False,
            attempts=attempts,
            total_time=time.perf_counter() - start,
            last_error=last_error,
            escalated=escalated,
        )

    def record(self, task_name: str, result: RetryResult):
        """Record a retry attempt for analytics."""
        self._history.append({
            "task_name": task_name,
            "success": result.success,
            "attempts": result.attempts,
            "total_time": result.total_time,
            "last_error": result.last_error,
            "escalated": result.escalated,
        })

    def stats(self) -> Dict[str, Any]:
        """Get retry statistics."""
        if not self._history:
            return {"total": 0, "success_rate": 0.0, "avg_attempts": 0.0}
        successes = sum(1 for h in self._history if h["success"])
        attempts = [h["attempts"] for h in self._history]
        return {
            "total": len(self._history),
            "successes": successes,
            "failures": len(self._history) - successes,
            "success_rate": successes / max(1, len(self._history)),
            "avg_attempts": sum(attempts) / max(1, len(attempts)),
            "escalated": sum(1 for h in self._history if h["escalated"]),
        }
