"""Runtime session management.

Each project execution gets a unique session with:
  - session ID, project name, goal
  - current phase, completed/pending tasks
  - artifacts, errors, logs
  - timestamps for start, completion, last activity
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class RuntimeSession:
    """Single runtime session for a project execution."""

    session_id: str = field(default_factory=lambda: f"session-{uuid.uuid4().hex[:12]}")
    project_name: str = ""
    goal: str = ""
    status: str = "pending"  # pending, running, completed, failed, paused, resumed
    current_phase: str = ""
    completed_tasks: List[str] = field(default_factory=list)
    pending_tasks: List[str] = field(default_factory=list)
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    last_activity_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "project_name": self.project_name,
            "goal": self.goal,
            "status": self.status,
            "current_phase": self.current_phase,
            "completed_tasks": list(self.completed_tasks),
            "pending_tasks": list(self.pending_tasks),
            "artifacts": list(self.artifacts),
            "errors": list(self.errors),
            "logs": list(self.logs),
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "last_activity_at": self.last_activity_at,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RuntimeSession:
        return cls(
            session_id=str(data.get("session_id", cls.__dataclass_fields__["session_id"].default_factory())),
            project_name=str(data.get("project_name", "")),
            goal=str(data.get("goal", "")),
            status=str(data.get("status", "pending")),
            current_phase=str(data.get("current_phase", "")),
            completed_tasks=list(data.get("completed_tasks", [])),
            pending_tasks=list(data.get("pending_tasks", [])),
            artifacts=list(data.get("artifacts", [])),
            errors=list(data.get("errors", [])),
            logs=list(data.get("logs", [])),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            last_activity_at=data.get("last_activity_at"),
            metadata=dict(data.get("metadata", {})),
        )


class RuntimeSessionManager:
    """Manage runtime sessions for project execution."""

    def __init__(self, sessions_dir: str = ".jarvis/sessions"):
        self.sessions_dir = sessions_dir
        os.makedirs(sessions_dir, exist_ok=True)
        self._sessions: Dict[str, RuntimeSession] = {}

    def create_session(self, project_name: str, goal: str, tasks: List[str]) -> RuntimeSession:
        """Create a new runtime session."""
        session = RuntimeSession(
            project_name=project_name,
            goal=goal,
            pending_tasks=list(tasks),
            started_at=datetime.now(timezone.utc).isoformat(),
            last_activity_at=datetime.now(timezone.utc).isoformat(),
        )
        self._sessions[session.session_id] = session
        self._save_session(session)
        return session

    def get_session(self, session_id: str) -> Optional[RuntimeSession]:
        """Get session by ID."""
        if session_id in self._sessions:
            return self._sessions[session_id]
        # Try loading from disk
        session = self._load_session(session_id)
        if session:
            self._sessions[session_id] = session
        return session

    def update_status(self, session_id: str, status: str):
        """Update session status."""
        session = self._get_or_load(session_id)
        if session:
            session.status = status
            session.last_activity_at = datetime.now(timezone.utc).isoformat()
            if status == "completed" and not session.completed_at:
                session.completed_at = datetime.now(timezone.utc).isoformat()
            self._save_session(session)

    def start_phase(self, session_id: str, phase: str):
        """Start a new phase."""
        session = self._get_or_load(session_id)
        if session:
            session.current_phase = phase
            session.last_activity_at = datetime.now(timezone.utc).isoformat()
            self._save_session(session)

    def complete_task(self, session_id: str, task_id: str):
        """Mark a task as completed."""
        session = self._get_or_load(session_id)
        if session:
            if task_id in session.pending_tasks:
                session.pending_tasks.remove(task_id)
            if task_id not in session.completed_tasks:
                session.completed_tasks.append(task_id)
            session.last_activity_at = datetime.now(timezone.utc).isoformat()
            self._save_session(session)

    def fail_task(self, session_id: str, task_id: str, error: str):
        """Mark a task as failed."""
        session = self._get_or_load(session_id)
        if session:
            session.errors.append(f"{task_id}: {error}")
            if task_id in session.pending_tasks:
                session.pending_tasks.remove(task_id)
            session.last_activity_at = datetime.now(timezone.utc).isoformat()
            self._save_session(session)

    def add_artifact(self, session_id: str, artifact: Dict[str, Any]):
        """Add artifact to session."""
        session = self._get_or_load(session_id)
        if session:
            session.artifacts.append(artifact)
            session.last_activity_at = datetime.now(timezone.utc).isoformat()
            self._save_session(session)

    def add_log(self, session_id: str, log: str):
        """Add log entry to session."""
        session = self._get_or_load(session_id)
        if session:
            session.logs.append(log)
            session.last_activity_at = datetime.now(timezone.utc).isoformat()
            self._save_session(session)

    def get_progress(self, session_id: str) -> Dict[str, Any]:
        """Get session progress."""
        session = self._get_or_load(session_id)
        if not session:
            return {}

        total = len(session.completed_tasks) + len(session.pending_tasks)
        completed = len(session.completed_tasks)
        progress_pct = (completed / max(1, total)) * 100

        return {
            "session_id": session_id,
            "status": session.status,
            "current_phase": session.current_phase,
            "completed": completed,
            "pending": len(session.pending_tasks),
            "total": total,
            "progress_percent": round(progress_pct, 1),
            "artifacts": len(session.artifacts),
            "errors": len(session.errors),
        }

    def list_sessions(self) -> List[str]:
        """List all session IDs."""
        return list(self._sessions.keys())

    def _get_or_load(self, session_id: str) -> Optional[RuntimeSession]:
        """Get session from memory or load from disk."""
        if session_id in self._sessions:
            return self._sessions[session_id]
        return self._load_session(session_id)

    def _load_session(self, session_id: str) -> Optional[RuntimeSession]:
        """Load session from disk."""
        path = os.path.join(self.sessions_dir, f"{session_id}.json")
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return RuntimeSession.from_dict(data)
        except (json.JSONDecodeError, TypeError):
            return None

    def _save_session(self, session: RuntimeSession):
        """Save session to disk."""
        path = os.path.join(self.sessions_dir, f"{session.session_id}.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(session.to_dict(), f, indent=2, default=str)
        except (OSError, TypeError):
            pass
