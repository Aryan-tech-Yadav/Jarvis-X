"""Typed task submitted to the EOS dispatcher."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from app.eos.priority import Priority
from app.eos.status import TaskStatus


@dataclass
class Task:
    capability: str
    entity: Any = None
    intent: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: Priority = Priority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    id: str = field(default_factory=lambda: uuid4().hex)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.priority = Priority(self.priority)
        self.status = TaskStatus(self.status)

