"""Thread-safe, priority-ordered agent mailbox."""

from __future__ import annotations

from collections import deque
from heapq import heappop, heappush
from itertools import count
from threading import Condition
from typing import List, Optional

from .message import AgentMessage


class Mailbox:
    """Inbox/outbox queues for one agent."""

    def __init__(self, owner: str):
        if not owner or not owner.strip():
            raise ValueError("Mailbox owner cannot be empty")
        self.owner = owner.strip()
        self._inbox = []
        self._outbox = deque()
        self._sequence = count()
        self._condition = Condition()

    def deliver(self, message: AgentMessage) -> None:
        if message.receiver != self.owner:
            raise ValueError(f"Message is addressed to {message.receiver}, not {self.owner}")
        with self._condition:
            heappush(self._inbox, (-int(message.priority), next(self._sequence), message))
            self._condition.notify()

    def send(self, message: AgentMessage) -> AgentMessage:
        if message.sender != self.owner:
            raise ValueError(f"Message sender is {message.sender}, not {self.owner}")
        with self._condition:
            self._outbox.append(message)
        return message

    def receive(self, timeout: Optional[float] = None) -> Optional[AgentMessage]:
        with self._condition:
            if not self._inbox and not self._condition.wait(timeout):
                return None
            if not self._inbox:
                return None
            return heappop(self._inbox)[2]

    def drain(self) -> List[AgentMessage]:
        with self._condition:
            messages = [heappop(self._inbox)[2] for _ in range(len(self._inbox))]
        return messages

    def drain_outbox(self) -> List[AgentMessage]:
        with self._condition:
            messages = list(self._outbox)
            self._outbox.clear()
        return messages

    @property
    def pending(self) -> int:
        with self._condition:
            return len(self._inbox)

