from __future__ import annotations

import heapq
from typing import Any, List, Optional


class AgentTaskQueue:
    """Priority task queue with transition validation, automatic retries, and dead-letter queue (DLQ)."""

    VALID_TRANSITIONS = {
        "pending": {"running", "cancelled"},
        "running": {"completed", "failed", "cancelled"},
        "failed": {"pending"},  # can re-enqueue on retry
        "completed": set(),
        "cancelled": set(),
    }

    def __init__(self, validate_transitions: bool = False):
        self._items = []
        self._sequence = 0
        self.dead_letter_queue: List[Any] = []
        self.validate_transitions = validate_transitions

    def _set_status(self, task: Any, target_status: str):
        current = getattr(task, "status", "pending")
        if current == target_status:
            return
        if self.validate_transitions:
            allowed = self.VALID_TRANSITIONS.get(current, set())
            if target_status not in allowed:
                raise ValueError(f"Invalid task transition from '{current}' to '{target_status}'")
        task.status = target_status

    def enqueue(self, task):
        if not hasattr(task, "priority"):
            raise TypeError("Task must expose a priority")
        self._set_status(task, "pending")
        self._sequence += 1
        heapq.heappush(self._items, (-task.priority, self._sequence, task))

    def dequeue(self):
        if not self._items:
            return None
        task = heapq.heappop(self._items)[2]
        self._set_status(task, "running")
        return task

    def complete(self, task, result=None):
        self._set_status(task, "completed")
        task.result = result
        return task

    def fail(self, task, result=None, auto_retry: bool = False):
        """Mark task as failed. If auto_retry is True and retries remain, re-enqueue; else DLQ."""
        self._set_status(task, "failed")
        task.result = result

        retry_count = getattr(task, "retry_count", 0)
        max_retries = getattr(task, "max_retries", 0)

        if auto_retry and retry_count < max_retries:
            task.retry_count = retry_count + 1
            self.enqueue(task)
        else:
            self.dead_letter_queue.append(task)

        return task

    def cancel(self, task):
        self._set_status(task, "cancelled")
        return task

    def get_dead_letter_tasks(self) -> List[Any]:
        return list(self.dead_letter_queue)

    def clear_dead_letter_queue(self):
        self.dead_letter_queue.clear()

    def peek(self):
        return self._items[0][2] if self._items else None

    def clear(self):
        self._items.clear()
        self.dead_letter_queue.clear()

    def __len__(self):
        return len(self._items)
