"""Shared project context for multi-agent engineering.

Every agent reads and updates this single context object instead of
passing function arguments around.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ProjectContext:
    """Mutable shared state for a single engineering project run."""

    goal: str = ""
    project_name: str = ""
    project_path: str = ""
    requirements: Dict[str, Any] = field(default_factory=dict)
    architecture: Dict[str, Any] = field(default_factory=dict)
    execution_plan: Dict[str, Any] = field(default_factory=dict)
    files: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    progress: List[Dict[str, Any]] = field(default_factory=list)
    current_task: str = ""
    completed_tasks: List[str] = field(default_factory=list)
    status: str = "pending"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal": self.goal,
            "project_name": self.project_name,
            "project_path": self.project_path,
            "requirements": dict(self.requirements),
            "architecture": dict(self.architecture),
            "execution_plan": dict(self.execution_plan),
            "files": list(self.files),
            "errors": list(self.errors),
            "logs": list(self.logs),
            "metrics": dict(self.metrics),
            "progress": dict(self.progress),
            "current_task": self.current_task,
            "completed_tasks": list(self.completed_tasks),
            "status": self.status,
            "metadata": dict(self.metadata),
        }

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def add_error(self, error: str):
        if error and error not in self.errors:
            self.errors.append(error)

    def add_log(self, log: str):
        if log and log not in self.logs:
            self.logs.append(log)

    def add_completed_task(self, task: str):
        if task and task not in self.completed_tasks:
            self.completed_tasks.append(task)

    def add_progress(self, agent: str, result: Any):
        """Add agent progress entry."""
        self.progress.append({"agent": agent, "result": result})

    def set_metric(self, key: str, value: Any):
        self.metrics[key] = value

    def summary(self) -> str:
        return (
            f"Project: {self.project_name or self.goal}\n"
            f"Status: {self.status}\n"
            f"Current Task: {self.current_task}\n"
            f"Path: {self.project_path}\n"
            f"Files: {len(self.files)}\n"
            f"Errors: {len(self.errors)}\n"
            f"Completed Tasks: {len(self.completed_tasks)}"
        )
