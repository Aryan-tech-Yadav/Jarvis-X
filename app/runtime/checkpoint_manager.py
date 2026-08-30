"""Checkpoint manager for crash recovery.

After each important phase, save a checkpoint.
If the runtime crashes, resume from the last checkpoint instead
of restarting the entire project.
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class Checkpoint:
    """Single project checkpoint."""

    checkpoint_id: str = field(default_factory=lambda: f"ckpt-{uuid.uuid4().hex[:12]}")
    session_id: str = ""
    project_name: str = ""
    goal: str = ""
    phase: str = ""
    status: str = "pending"
    completed_tasks: List[str] = field(default_factory=list)
    pending_tasks: List[str] = field(default_factory=list)
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    sequence: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "checkpoint_id": self.checkpoint_id,
            "session_id": self.session_id,
            "project_name": self.project_name,
            "goal": self.goal,
            "phase": self.phase,
            "status": self.status,
            "completed_tasks": list(self.completed_tasks),
            "pending_tasks": list(self.pending_tasks),
            "artifacts": list(self.artifacts),
            "errors": list(self.errors),
            "logs": list(self.logs),
            "metrics": dict(self.metrics),
            "created_at": self.created_at,
            "sequence": self.sequence,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Checkpoint:
        return cls(
            checkpoint_id=str(data.get("checkpoint_id", cls.__dataclass_fields__["checkpoint_id"].default_factory())),
            session_id=str(data.get("session_id", "")),
            project_name=str(data.get("project_name", "")),
            goal=str(data.get("goal", "")),
            phase=str(data.get("phase", "")),
            status=str(data.get("status", "pending")),
            completed_tasks=list(data.get("completed_tasks", [])),
            pending_tasks=list(data.get("pending_tasks", [])),
            artifacts=list(data.get("artifacts", [])),
            errors=list(data.get("errors", [])),
            logs=list(data.get("logs", [])),
            metrics=dict(data.get("metrics", {})),
            created_at=str(data.get("created_at", "")),
            sequence=int(data.get("sequence", 0)),
            metadata=dict(data.get("metadata", {})),
        )


class CheckpointManager:
    """Persist and resume project checkpoints."""

    def __init__(self, checkpoints_dir: str = ".jarvis/checkpoints"):
        self.checkpoints_dir = checkpoints_dir
        os.makedirs(checkpoints_dir, exist_ok=True)
        self._checkpoints: Dict[str, Checkpoint] = {}
        self._sequence = 0
        self._load()

    def _load(self):
        if not os.path.isdir(self.checkpoints_dir):
            return
        entries = []
        max_seq = 0
        for filename in os.listdir(self.checkpoints_dir):
            if not filename.endswith(".json"):
                continue
            path = os.path.join(self.checkpoints_dir, filename)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                ckpt = Checkpoint.from_dict(data)
                max_seq = max(max_seq, ckpt.sequence)
                entries.append(ckpt)
            except (OSError, json.JSONDecodeError, TypeError):
                pass
        self._sequence = max_seq
        entries.sort(key=lambda c: (c.created_at, c.sequence))
        for ckpt in entries:
            self._checkpoints[ckpt.checkpoint_id] = ckpt

    def save(self, checkpoint: Checkpoint) -> str:
        """Save a checkpoint and return its ID."""
        self._checkpoints[checkpoint.checkpoint_id] = checkpoint
        path = os.path.join(self.checkpoints_dir, f"{checkpoint.checkpoint_id}.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(checkpoint.to_dict(), f, indent=2, default=str)
        except (OSError, TypeError):
            pass
        return checkpoint.checkpoint_id

    def latest(self, session_id: Optional[str] = None) -> Optional[Checkpoint]:
        """Get the latest checkpoint, optionally filtered by session."""
        if session_id:
            candidates = [c for c in self._checkpoints.values() if c.session_id == session_id]
        else:
            candidates = list(self._checkpoints.values())
        if not candidates:
            return None
        return max(candidates, key=lambda c: (c.sequence, c.created_at))

    def load(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """Load a checkpoint by ID."""
        if checkpoint_id in self._checkpoints:
            return self._checkpoints[checkpoint_id]
        path = os.path.join(self.checkpoints_dir, f"{checkpoint_id}.json")
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            ckpt = Checkpoint.from_dict(data)
            self._checkpoints[checkpoint_id] = ckpt
            return ckpt
        except (json.JSONDecodeError, TypeError):
            return None

    def create_checkpoint(self, session_id: str, project_name: str, goal: str,
                          phase: str, completed_tasks: List[str], pending_tasks: List[str],
                          artifacts: Optional[List[Dict[str, Any]]] = None,
                          errors: Optional[List[str]] = None,
                          logs: Optional[List[str]] = None,
                          metrics: Optional[Dict[str, Any]] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> Checkpoint:
        """Create and save a new checkpoint."""
        self._sequence += 1
        checkpoint = Checkpoint(
            session_id=session_id,
            project_name=project_name,
            goal=goal,
            phase=phase,
            completed_tasks=list(completed_tasks),
            pending_tasks=list(pending_tasks),
            artifacts=list(artifacts or []),
            errors=list(errors or []),
            logs=list(logs or []),
            metrics=dict(metrics or {}),
            sequence=self._sequence,
            metadata=dict(metadata or {}),
        )
        return self.save(checkpoint)

    def list_checkpoints(self, session_id: Optional[str] = None) -> List[str]:
        """List checkpoint IDs, optionally filtered by session."""
        if session_id:
            return [cid for cid, ckpt in self._checkpoints.items() if ckpt.session_id == session_id]
        return list(self._checkpoints.keys())

    def can_resume(self, session_id: str) -> bool:
        """Check if there is a resumable checkpoint for the session."""
        return self.latest(session_id) is not None
