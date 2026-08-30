from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any


@dataclass
class AgentMessage:
    sender: str
    receiver: str
    message_type: str
    payload: Any = None

    @property
    def from_(self):
        return self.sender

    @property
    def to(self):
        return self.receiver

    @property
    def type(self):
        return self.message_type

    @property
    def data(self):
        return self.payload

    def to_dict(self):
        return {"from": self.sender, "to": self.receiver, "type": self.message_type, "data": self.payload}


class MessageBus:
    def __init__(self):
        self._queues = defaultdict(deque)

    def send(self, sender, receiver, message_type, payload=None, priority=0, timeout=None, retries=0):
        if not isinstance(sender, str) or not sender.strip():
            raise ValueError("Message sender cannot be empty")
        if not isinstance(receiver, str) or not receiver.strip():
            raise ValueError("Message receiver cannot be empty")
        if not isinstance(message_type, str) or not message_type.strip():
            raise ValueError("Message type cannot be empty")
        message = AgentMessage(sender, receiver, message_type, payload)
        message.priority = priority
        message.timeout = timeout
        message.retries = retries
        self._queues[receiver].append(message)
        return message

    def broadcast(self, sender, receivers, message_type, payload=None, priority=0):
        return [self.send(sender, receiver, message_type, payload, priority) for receiver in receivers]

    def reply(self, message, sender, payload=None):
        return self.send(sender, message.sender, "REPLY", payload)

    def receive(self, receiver):
        return self._queues[receiver].popleft() if self._queues[receiver] else None

    def pending(self, receiver):
        return len(self._queues[receiver])

    def route(self, message):
        """Route a serializable milestone message dictionary."""
        if not isinstance(message, dict):
            raise TypeError("Message must be a dictionary")
        required = ("from", "to", "type")
        if any(not message.get(key) for key in required):
            raise ValueError("Message requires from, to, and type")
        return self.send(message["from"], message["to"], message["type"], message.get("data"))
