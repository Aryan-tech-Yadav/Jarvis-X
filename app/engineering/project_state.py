"""Project state tracker for engineering workflow.

Maintains real-time state of project execution including
current task, progress, failures, and metrics.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class ProjectState:
    """Current state of an engineering project."""

    project_id: str
    project_name: str
    current_task: Optional[str] = None
    current_phase: Optional[str] = None
    status: str = "pending"  # pending, in_progress, completed, failed, paused
    completed_tasks: List[str] = field(default_factory=list)
    failed_tasks: List[str] = field(default_factory=list)
    pending_tasks: List[str] = field(default_factory=list)
    created_files: List[str] = field(default_factory=list)
    test_coverage: float = 0.0
    runtime_errors: List[str] = field(default_factory=list)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "current_task": self.current_task,
            "current_phase": self.current_phase,
            "status": self.status,
            "completed_tasks": list(self.completed_tasks),
            "failed_tasks": list(self.failed_tasks),
            "pending_tasks": list(self.pending_tasks),
            "created_files": list(self.created_files),
            "test_coverage": round(self.test_coverage, 1),
            "runtime_errors": list(self.runtime_errors),
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "metadata": dict(self.metadata),
        }


class ProjectStateManager:
    """Manage project execution state.

    Tracks progress, handles failures, and maintains metrics
    throughout the engineering workflow.
    """

    def __init__(self, state_dir: str = ".jarvis/states"):
        self.state_dir = state_dir
        os.makedirs(state_dir, exist_ok=True)
        self._states: Dict[str, ProjectState] = {}

    def create_project(self, project_id: str, project_name: str, tasks: List[str]) -> ProjectState:
        """Create a new project state.

        Args:
            project_id: Unique project identifier.
            project_name: Human-readable project name.
            tasks: List of task IDs.

        Returns:
            ProjectState for the new project.
        """
        state = ProjectState(
            project_id=project_id,
            project_name=project_name,
            pending_tasks=list(tasks),
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        self._states[project_id] = state
        self._save_state(state)
        return state

    def get_state(self, project_id: str) -> Optional[ProjectState]:
        """Get project state by ID."""
        return self._get_or_load(project_id)

    def update_status(self, project_id: str, status: str):
        """Update project status."""
        state = self._get_or_load(project_id)
        if state:
            state.status = status
            if status == "completed" and not state.completed_at:
                state.completed_at = datetime.now(timezone.utc).isoformat()
            self._save_state(state)

    def start_task(self, project_id: str, task_id: str):
        """Mark a task as started."""
        state = self._get_or_load(project_id)
        if state:
            state.current_task = task_id
            state.status = "in_progress"
            if task_id in state.pending_tasks:
                state.pending_tasks.remove(task_id)
            self._save_state(state)

    def complete_task(self, project_id: str, task_id: str, files_created: List[str] = None):
        """Mark a task as completed."""
        state = self._get_or_load(project_id)
        if state:
            state.current_task = None
            state.completed_tasks.append(task_id)
            if task_id in state.pending_tasks:
                state.pending_tasks.remove(task_id)
            if files_created:
                state.created_files.extend(files_created)
            self._save_state(state)

    def fail_task(self, project_id: str, task_id: str, error: str):
        """Mark a task as failed."""
        state = self._get_or_load(project_id)
        if state:
            state.failed_tasks.append(task_id)
            state.runtime_errors.append(f"{task_id}: {error}")
            if task_id in state.pending_tasks:
                state.pending_tasks.remove(task_id)
            self._save_state(state)

    def set_phase(self, project_id: str, phase: str):
        """Update current phase."""
        state = self._get_or_load(project_id)
        if state:
            state.current_phase = phase
            self._save_state(state)

    def update_coverage(self, project_id: str, coverage: float):
        """Update test coverage."""
        state = self._get_or_load(project_id)
        if state:
            state.test_coverage = max(state.test_coverage, coverage)
            self._save_state(state)

    def add_files(self, project_id: str, files: List[str]):
        """Add created files to state."""
        state = self._get_or_load(project_id)
        if state:
            state.created_files.extend(files)
            self._save_state(state)

    def get_progress(self, project_id: str) -> dict:
        """Get project progress metrics."""
        state = self._get_or_load(project_id)
        if not state:
            return {}

        total = len(state.completed_tasks) + len(state.failed_tasks) + len(state.pending_tasks)
        completed = len(state.completed_tasks)
        failed = len(state.failed_tasks)
        progress_pct = (completed / max(1, total)) * 100

        return {
            "project_id": project_id,
            "status": state.status,
            "completed": completed,
            "failed": failed,
            "pending": len(state.pending_tasks),
            "total": total,
            "progress_percent": round(progress_pct, 1),
            "test_coverage": state.test_coverage,
            "current_task": state.current_task,
            "current_phase": state.current_phase,
            "files_created": len(state.created_files),
            "errors": len(state.runtime_errors),
        }

    def _get_or_load(self, project_id: str) -> Optional[ProjectState]:
        """Get state from memory or load from disk."""
        if project_id in self._states:
            return self._states[project_id]

        # Try loading from disk
        state_path = os.path.join(self.state_dir, f"{project_id}.json")
        if os.path.exists(state_path):
            try:
                with open(state_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                state = ProjectState(**data)
                self._states[project_id] = state
                return state
            except (json.JSONDecodeError, TypeError):
                return None
        return None

    def _save_state(self, state: ProjectState):
        """Save state to disk."""
        state_path = os.path.join(self.state_dir, f"{state.project_id}.json")
        try:
            with open(state_path, "w", encoding="utf-8") as f:
                json.dump(state.to_dict(), f, indent=2, default=str)
        except (OSError, TypeError):
            pass
