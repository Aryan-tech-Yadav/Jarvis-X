"""Bounded agent-local memory."""

from collections import deque
from typing import Any, Deque, List


class AgentMemory:
    def __init__(self, limit: int = 100):
        if limit < 1:
            raise ValueError("memory limit must be positive")
        self._items: Deque[Any] = deque(maxlen=limit)

    def remember(self, item: Any) -> None:
        self._items.append(item)

    def snapshot(self) -> List[Any]:
        return list(self._items)

