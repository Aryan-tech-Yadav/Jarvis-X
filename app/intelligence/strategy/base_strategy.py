"""Strategy plugin contract."""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseStrategy(ABC):
    name = "strategy"
    version = "1.0"

    @abstractmethod
    def matches(self, context: Dict[str, Any]) -> bool:
        """Return whether this strategy applies to the project context."""

    @abstractmethod
    def describe(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Return a serializable strategy candidate."""

