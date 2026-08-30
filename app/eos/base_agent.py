"""Stable contract for agents managed by the EOS kernel."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Iterable, Tuple

from app.core.logger import Logger


class AgentStatus(str, Enum):
    IDLE = "idle"
    READY = "ready"
    BUSY = "busy"
    FAILED = "failed"
    STOPPED = "stopped"
    OFFLINE = "offline"


class BaseAgent(ABC):
    """Lifecycle and capability contract for EOS agents."""

    name: str = "agent"
    version: str = "1.0"
    capabilities: Tuple[str, ...] = ()
    enabled: bool = True
    status: AgentStatus = AgentStatus.IDLE

    def __init__(self) -> None:
        self.status = AgentStatus.IDLE

    def initialize(self) -> bool:
        self.status = AgentStatus.READY
        Logger.info(f"[EOS] Agent initialized: {self.name}")
        return True

    def load(self) -> bool:
        return self.initialize()

    @abstractmethod
    def execute(self, task: Any) -> Any:
        """Execute a task and return an AgentResult-compatible value."""

    def pause(self) -> bool:
        self.status = AgentStatus.IDLE
        return True

    def resume(self) -> bool:
        self.status = AgentStatus.READY
        return True

    def shutdown(self) -> bool:
        self.status = AgentStatus.STOPPED
        Logger.info(f"[EOS] Agent stopped: {self.name}")
        return True

    def health_check(self) -> bool:
        return self.enabled and self.status not in {
            AgentStatus.FAILED,
            AgentStatus.STOPPED,
            AgentStatus.OFFLINE,
        }

    def supports(self, capability: str) -> bool:
        requested = capability.casefold()
        return requested in {item.casefold() for item in self.capabilities}

    def learn(self, lesson: Any) -> None:
        """Hook for agent-specific learning implementations."""

    def reflect(self, reflection: Any) -> None:
        """Hook for agent-specific post-execution reflection."""
