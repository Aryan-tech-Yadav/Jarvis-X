from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, List, Optional


@dataclass
class AgentTask:
    title: str
    agent: str
    priority: int = 0
    status: str = "pending"
    result: Any = None
    history: List[Any] = field(default_factory=list)
    task_id: str = field(default_factory=lambda: f"task-{uuid.uuid4().hex[:8]}")
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    max_retries: int = 3
    retry_count: int = 0
    error: Optional[str] = None
