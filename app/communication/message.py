"""Typed messages exchanged by agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import IntEnum
from typing import Any, Dict, Optional
from uuid import uuid4


class MessagePriority(IntEnum):
    """Higher values are delivered before lower values."""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class AgentMessage:
    sender: str
    receiver: str
    message_type: str
    payload: Any = None
    priority: int = MessagePriority.NORMAL
    message_id: str = field(default_factory=lambda: uuid4().hex)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    expires_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for field_name in ("sender", "receiver", "message_type"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Message {field_name} cannot be empty")
            setattr(self, field_name, value.strip())
        self.priority = int(self.priority)

    @property
    def from_(self) -> str:
        return self.sender

    @property
    def to(self) -> str:
        return self.receiver

    @property
    def type(self) -> str:
        return self.message_type

    @property
    def data(self) -> Any:
        return self.payload

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "from": self.sender,
            "to": self.receiver,
            "type": self.message_type,
            "data": self.payload,
            "priority": self.priority,
            "created_at": self.created_at,
            "correlation_id": self.correlation_id,
            "reply_to": self.reply_to,
            "expires_at": self.expires_at,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, value: Dict[str, Any]) -> "AgentMessage":
        return cls(
            sender=value["from"],
            receiver=value["to"],
            message_type=value["type"],
            payload=value.get("data", value.get("payload")),
            priority=value.get("priority", MessagePriority.NORMAL),
            message_id=value.get("message_id", uuid4().hex),
            created_at=value.get("created_at", datetime.now(timezone.utc).isoformat()),
            correlation_id=value.get("correlation_id"),
            reply_to=value.get("reply_to"),
            expires_at=value.get("expires_at"),
            metadata=dict(value.get("metadata", {})),
        )

