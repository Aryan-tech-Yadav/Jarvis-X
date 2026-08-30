"""Audit Timeline with chronological action tracing."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4


@dataclass
class TimelineEvent:
    event_id: str = field(default_factory=lambda: str(uuid4()))
    stage: str = "general"
    action: str = ""
    actor: str = "Jarvis-X"
    details: Dict[str, Any] = field(default_factory=dict)
    duration_sec: float = 0.0
    status: str = "SUCCESS"  # SUCCESS, FAILED, WARNING, IN_PROGRESS
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "stage": self.stage,
            "action": self.action,
            "actor": self.actor,
            "details": dict(self.details),
            "duration_sec": round(float(self.duration_sec), 3),
            "status": self.status,
            "timestamp": self.timestamp,
        }


class AuditTimeline:
    """Manages an unbroken audit trail of all actions, states, and transitions."""

    def __init__(self):
        self._events: List[TimelineEvent] = []

    def record_event(
        self,
        stage: str,
        action: str,
        actor: str = "Jarvis-X",
        details: Optional[Dict[str, Any]] = None,
        duration_sec: float = 0.0,
        status: str = "SUCCESS",
    ) -> TimelineEvent:
        event = TimelineEvent(
            stage=stage,
            action=action,
            actor=actor,
            details=details or {},
            duration_sec=duration_sec,
            status=status,
        )
        self._events.append(event)
        return event

    def get_events(self) -> List[TimelineEvent]:
        return list(self._events)

    def to_dict(self) -> List[Dict[str, Any]]:
        return [e.to_dict() for e in self._events]

    def to_markdown(self) -> str:
        lines = [
            "### ⏱️ Audit Execution Timeline",
            "",
            "| Time | Stage | Action | Actor | Status | Duration |",
            "| :--- | :--- | :--- | :--- | :---: | :---: |",
        ]
        for e in self._events:
            t = e.timestamp.split("T")[-1][:8] if "T" in e.timestamp else e.timestamp
            badge = "🟢 PASS" if e.status == "SUCCESS" else ("🔴 FAIL" if e.status == "FAILED" else "⚠️ WARN")
            lines.append(f"| `{t}` | `{e.stage}` | **{e.action}** | `{e.actor}` | {badge} | `{e.duration_sec:.2f}s` |")
        return "\n".join(lines)
