"""Runtime events for observability and analytics.

Every runtime action emits an event:
  PROJECT_STARTED
  AGENT_STARTED
  AGENT_FINISHED
  TEST_FAILED
  REPAIR_SUCCESS
  DEPLOYMENT_COMPLETE
  ...
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional


@dataclass
class RuntimeEvent:
    """Single runtime event."""

    event_id: str = field(default_factory=lambda: f"evt-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}")
    event_type: str = ""
    session_id: str = ""
    phase: str = ""
    agent: str = ""
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "session_id": self.session_id,
            "phase": self.phase,
            "agent": self.agent,
            "message": self.message,
            "data": dict(self.data),
            "created_at": self.created_at,
        }


class RuntimeEventBus:
    """In-process event bus for runtime events."""

    def __init__(self, events_path: str = ".jarvis/events/runtime_events.jsonl"):
        self.events_path = events_path
        self._subscribers: List[Callable[[RuntimeEvent], None]] = []
        os.makedirs(os.path.dirname(events_path) or ".", exist_ok=True)

    def subscribe(self, handler: Callable[[RuntimeEvent], None]):
        """Subscribe to runtime events."""
        self._subscribers.append(handler)

    def publish(self, event_type: str, session_id: str = "", phase: str = "",
                agent: str = "", message: str = "", data: Optional[Dict[str, Any]] = None):
        """Publish a runtime event."""
        event = RuntimeEvent(
            event_type=event_type,
            session_id=session_id,
            phase=phase,
            agent=agent,
            message=message,
            data=data or {},
        )
        self._persist(event)
        for handler in self._subscribers:
            try:
                handler(event)
            except Exception:
                pass
        return event

    def history(self, event_type: Optional[str] = None, session_id: Optional[str] = None,
                limit: int = 100) -> List[RuntimeEvent]:
        """Load event history from disk."""
        events: List[RuntimeEvent] = []
        if not os.path.exists(self.events_path):
            return events
        try:
            with open(self.events_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        event = RuntimeEvent(**data)
                        if event_type and event.event_type != event_type:
                            continue
                        if session_id and event.session_id != session_id:
                            continue
                        events.append(event)
                    except (json.JSONDecodeError, TypeError):
                        continue
        except OSError:
            pass
        events.sort(key=lambda e: e.created_at, reverse=True)
        return events[:limit]

    def _persist(self, event: RuntimeEvent):
        """Append event to disk."""
        try:
            with open(self.events_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event.to_dict(), default=str) + "\n")
        except OSError:
            pass
