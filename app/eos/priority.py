"""Priority values used by EOS task scheduling."""

from enum import IntEnum
from heapq import heappop, heappush
from itertools import count
from typing import List, Tuple


class Priority(IntEnum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class PriorityQueue:
    """Small FIFO-stable max-priority queue for pending tasks."""

    def __init__(self) -> None:
        self._items: List[Tuple[int, int, object]] = []
        self._sequence = count()

    def put(self, task: object) -> None:
        priority = int(getattr(task, "priority", Priority.NORMAL))
        heappush(self._items, (-priority, next(self._sequence), task))

    def get(self) -> object:
        if not self._items:
            raise IndexError("Priority queue is empty")
        return heappop(self._items)[2]

    def __len__(self) -> int:
        return len(self._items)
