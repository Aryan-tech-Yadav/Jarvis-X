"""Retry policy for agent execution."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RetryPolicy:
    max_retry: int = 0
    delay: float = 0.0
    backoff: float = 1.0

    def __post_init__(self) -> None:
        if self.max_retry < 0:
            raise ValueError("max_retry cannot be negative")
        if self.delay < 0 or self.backoff < 1:
            raise ValueError("delay must be non-negative and backoff must be at least 1")

