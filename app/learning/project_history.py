"""Project history for learning and reuse.

Stores past project executions so that future similar projects
can reuse architecture, prompts, and lessons learned.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class ProjectHistoryEntry:
    """Single project execution record."""

    entry_id: str = field(default_factory=lambda: f"hist-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}")
    project_name: str = ""
    goal: str = ""
    status: str = ""
    duration: float = 0.0
    files_generated: int = 0
    tests_count: int = 0
    repair_count: int = 0
    warnings: int = 0
    errors: int = 0
    overall_score: float = 0.0
    architecture: Dict[str, Any] = field(default_factory=dict)
    agent_sequence: List[str] = field(default_factory=list)
    mistakes: List[str] = field(default_factory=list)
    fixes: List[str] = field(default_factory=list)
    prompts: List[str] = field(default_factory=list)
    success_rate: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "project_name": self.project_name,
            "goal": self.goal,
            "status": self.status,
            "duration": self.duration,
            "files_generated": self.files_generated,
            "tests_count": self.tests_count,
            "repair_count": self.repair_count,
            "warnings": self.warnings,
            "errors": self.errors,
            "overall_score": self.overall_score,
            "architecture": dict(self.architecture),
            "agent_sequence": list(self.agent_sequence),
            "mistakes": list(self.mistakes),
            "fixes": list(self.fixes),
            "prompts": list(self.prompts),
            "success_rate": self.success_rate,
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProjectHistoryEntry:
        return cls(
            entry_id=str(data.get("entry_id", "")),
            project_name=str(data.get("project_name", "")),
            goal=str(data.get("goal", "")),
            status=str(data.get("status", "")),
            duration=float(data.get("duration", 0.0)),
            files_generated=int(data.get("files_generated", 0)),
            tests_count=int(data.get("tests_count", 0)),
            repair_count=int(data.get("repair_count", 0)),
            warnings=int(data.get("warnings", 0)),
            errors=int(data.get("errors", 0)),
            overall_score=float(data.get("overall_score", 0.0)),
            architecture=dict(data.get("architecture", {})),
            agent_sequence=list(data.get("agent_sequence", [])),
            mistakes=list(data.get("mistakes", [])),
            fixes=list(data.get("fixes", [])),
            prompts=list(data.get("prompts", [])),
            success_rate=float(data.get("success_rate", 0.0)),
            created_at=str(data.get("created_at", "")),
            metadata=dict(data.get("metadata", {})),
        )


class ProjectHistory:
    """Persistent project execution history."""

    def __init__(self, history_path: str = "data/project_history.json"):
        self.history_path = history_path
        self._entries: List[ProjectHistoryEntry] = []
        os.makedirs(os.path.dirname(history_path) or ".", exist_ok=True)
        self._load()

    def _load(self):
        if not os.path.exists(self.history_path):
            return
        try:
            with open(self.history_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            if isinstance(raw, list):
                self._entries = [ProjectHistoryEntry.from_dict(item)
                                 for item in raw if isinstance(item, dict)]
        except (OSError, json.JSONDecodeError, TypeError):
            pass

    def _save(self):
        try:
            with open(self.history_path, "w", encoding="utf-8") as f:
                json.dump([entry.to_dict() for entry in self._entries], f, indent=2, default=str)
        except OSError:
            pass

    def add(self, entry: ProjectHistoryEntry) -> ProjectHistoryEntry:
        """Add a history entry."""
        self._entries.append(entry)
        self._save()
        return entry

    def record_execution(self, project_name: str, goal: str, status: str,
                         duration: float, overall_score: float = 0.0,
                         files_generated: int = 0, tests_count: int = 0,
                         repair_count: int = 0, warnings: int = 0, errors: int = 0,
                         architecture: Optional[Dict[str, Any]] = None,
                         agent_sequence: Optional[List[str]] = None,
                         mistakes: Optional[List[str]] = None,
                         fixes: Optional[List[str]] = None,
                         prompts: Optional[List[str]] = None,
                         success_rate: float = 0.0,
                         metadata: Optional[Dict[str, Any]] = None) -> ProjectHistoryEntry:
        """Record a project execution."""
        entry = ProjectHistoryEntry(
            project_name=project_name,
            goal=goal,
            status=status,
            duration=duration,
            overall_score=overall_score,
            files_generated=files_generated,
            tests_count=tests_count,
            repair_count=repair_count,
            warnings=warnings,
            errors=errors,
            architecture=architecture or {},
            agent_sequence=agent_sequence or [],
            mistakes=mistakes or [],
            fixes=fixes or [],
            prompts=prompts or [],
            success_rate=success_rate,
            metadata=metadata or {},
        )
        return self.add(entry)

    def find_similar(self, goal: str, limit: int = 5) -> List[ProjectHistoryEntry]:
        """Find similar past projects by goal."""
        words = set(goal.casefold().split())
        scored = []
        for entry in self._entries:
            haystack = f"{entry.project_name} {entry.goal}".casefold()
            score = sum(word in haystack for word in words)
            if score:
                scored.append((score, entry))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [entry for _, entry in scored[:max(1, limit)]]

    def stats(self) -> Dict[str, Any]:
        """Get aggregate statistics."""
        total = len(self._entries)
        if total == 0:
            return {"total": 0}
        successes = sum(1 for e in self._entries if e.status == "completed")
        return {
            "total": total,
            "successes": successes,
            "failures": total - successes,
            "success_rate": successes / total,
            "avg_duration": sum(e.duration for e in self._entries) / total,
            "avg_score": sum(e.overall_score for e in self._entries) / total,
            "total_repairs": sum(e.repair_count for e in self._entries),
        }

    def all_entries(self) -> List[ProjectHistoryEntry]:
        return list(self._entries)
