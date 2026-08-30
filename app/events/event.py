from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4


@dataclass
class Event:
    event_type: str
    payload: Any = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    event_id: str = field(default_factory=lambda: uuid4().hex)
    source: str = "system"
    target: Optional[str] = None
    priority: int = 2
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def timestamp(self) -> str:
        return self.created_at

    def to_dict(self):
        return {
            "event_id": self.event_id,
            "type": self.event_type,
            "source": self.source,
            "target": self.target,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "priority": self.priority,
            "metadata": dict(self.metadata),
        }