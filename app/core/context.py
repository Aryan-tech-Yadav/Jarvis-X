"""Shared state primitives for an engineering run."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class JarvisContext:
    """Cross-cutting fields common to planning, execution, and reporting."""

    goal: str
    project_path: Optional[str] = None
    current_step: Optional[str] = None
    memory: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    artifacts: List[Any] = field(default_factory=list)
    events: List[Dict[str, Any]] = field(default_factory=list)
    timeline: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        if not isinstance(self.goal, str) or not self.goal.strip():
            raise ValueError("Goal cannot be empty")
        self.goal = self.goal.strip()

    def start_step(self, step):
        self.current_step = str(step)
        entry = {"step": self.current_step, "started_at": self._now(), "status": "running"}
        self.timeline.append(entry)
        return entry

    def finish_step(self, entry, success=True, message=""):
        entry["finished_at"] = self._now()
        entry["status"] = "completed" if success else "failed"
        if message:
            entry["message"] = str(message)
        return entry

    def add_metric(self, name, value=1):
        key = str(name)
        self.metrics[key] = self.metrics.get(key, 0) + value
        return self.metrics[key]

    def add_event(self, event_type, payload=None):
        event = {"type": str(event_type), "payload": payload, "created_at": self._now()}
        self.events.append(event)
        return event

    def as_dict(self):
        return {
            "goal": self.goal,
            "project_path": self.project_path,
            "current_step": self.current_step,
            "memory": dict(self.memory),
            "metrics": dict(self.metrics),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "artifacts": list(self.artifacts),
            "events": list(self.events),
            "timeline": list(self.timeline),
        }

    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat()
