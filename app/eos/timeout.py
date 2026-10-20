"""Timeout configuration for agent execution."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TimeoutPolicy:
    seconds: Optional[float] = None

    def __post_init__(self) -> None:
        if self.seconds is not None and self.seconds <= 0:
            raise ValueError("timeout must be greater than zero")

