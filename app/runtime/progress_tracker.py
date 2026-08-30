"""Live progress tracker for engineering tasks.

Tracks task states:
  pending -> ready -> running -> completed
                               -> failed -> retrying -> completed
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class TaskState(str, Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    RETRYING = "retrying"
    SKIPPED = "skipped"


@dataclass
class TaskProgress:
    """Progress record for a single task."""

    task_id: str
    name: str
    state: TaskState = TaskState.PENDING
    agent: str = ""
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    attempts: int = 0
    max_retries: int = 3
    error: Optional[str] = None
    output: Optional[str] = None
    artifacts: List[str] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "state": self.state.value,
            "agent": self.agent,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "attempts": self.attempts,
            "max_retries": self.max_retries,
            "error": self.error,
            "output": self.output,
            "artifacts": list(self.artifacts),
            "logs": list(self.logs),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TaskProgress:
        state = data.get("state", TaskState.PENDING.value)
        try:
            task_state = TaskState(state)
        except ValueError:
            task_state = TaskState.PENDING
        return cls(
            task_id=str(data.get("task_id", "")),
            name=str(data.get("name", "")),
            state=task_state,
            agent=str(data.get("agent", "")),
            started_at=data.get("started_at"),
            finished_at=data.get("finished_at"),
            attempts=int(data.get("attempts", 0)),
            max_retries=int(data.get("max_retries", 3)),
            error=data.get("error"),
            output=data.get("output"),
            artifacts=list(data.get("artifacts", [])),
            logs=list(data.get("logs", [])),
        )


class ProgressTracker:
    """Track and persist live progress for all engineering tasks."""

    def __init__(self, progress_path: str = "progress.json"):
        self.progress_path = progress_path
        self._tasks: Dict[str, TaskProgress] = {}
        self._load()

    def _load(self):
        if os.path.isfile(self.progress_path):
            try:
                with open(self.progress_path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                if isinstance(raw, dict):
                    for task_id, data in raw.items():
                        self._tasks[task_id] = TaskProgress.from_dict(data)
            except (OSError, json.JSONDecodeError, TypeError):
                pass

    def _save(self):
        os.makedirs(os.path.dirname(self.progress_path) or ".", exist_ok=True)
        payload = {task_id: task.to_dict() for task_id, task in self._tasks.items()}
        with open(self.progress_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, default=str)

    def register_task(self, task_id: str, name: str, agent: str = "", max_retries: int = 3) -> TaskProgress:
        if task_id in self._tasks:
            return self._tasks[task_id]
        task = TaskProgress(task_id=task_id, name=name, agent=agent, max_retries=max_retries)
        self._tasks[task_id] = task
        self._save()
        return task

    def start(self, task_id: str):
        task = self._tasks.get(task_id)
        if task:
            task.state = TaskState.RUNNING
            task.started_at = datetime.now(timezone.utc).isoformat()
            task.attempts += 1
            self._save()

    def complete(self, task_id: str, output: Optional[str] = None, artifacts: Optional[List[str]] = None):
        task = self._tasks.get(task_id)
        if task:
            task.state = TaskState.COMPLETED
            task.finished_at = datetime.now(timezone.utc).isoformat()
            task.output = output
            if artifacts:
                task.artifacts.extend(artifacts)
            self._save()

    def fail(self, task_id: str, error: str):
        task = self._tasks.get(task_id)
        if task:
            task.state = TaskState.FAILED
            task.error = error
            task.finished_at = datetime.now(timezone.utc).isoformat()
            self._save()

    def retry(self, task_id: str):
        task = self._tasks.get(task_id)
        if task:
            task.state = TaskState.RETRYING
            task.error = None
            task.finished_at = None
            self._save()

    def skip(self, task_id: str, reason: str = ""):
        task = self._tasks.get(task_id)
        if task:
            task.state = TaskState.SKIPPED
            task.finished_at = datetime.now(timezone.utc).isoformat()
            task.error = reason
            self._save()

    def block(self, task_id: str, reason: str = ""):
        task = self._tasks.get(task_id)
        if task:
            task.state = TaskState.BLOCKED
            task.error = reason
            self._save()

    def add_log(self, task_id: str, log: str):
        task = self._tasks.get(task_id)
        if task:
            task.logs.append(log)
            self._save()

    def get(self, task_id: str) -> Optional[TaskProgress]:
        return self._tasks.get(task_id)

    def all_tasks(self) -> Dict[str, TaskProgress]:
        return dict(self._tasks)

    def summary(self) -> Dict[str, Any]:
        states: Dict[str, int] = {}
        for task in self._tasks.values():
            states[task.state.value] = states.get(task.state.value, 0) + 1
        return {
            "total": len(self._tasks),
            "states": states,
            "completed": states.get(TaskState.COMPLETED.value, 0),
            "failed": states.get(TaskState.FAILED.value, 0),
            "running": states.get(TaskState.RUNNING.value, 0),
            "pending": states.get(TaskState.PENDING.value, 0),
        }
