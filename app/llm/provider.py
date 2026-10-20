from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class LLMProvider(ABC):
    name = "provider"

    @abstractmethod
    def complete(self, prompt: str, model: Optional[str] = None, **kwargs: Any) -> str:
        """Return a completion for a prompt or raise a provider error."""

    def available(self) -> bool:
        return True
