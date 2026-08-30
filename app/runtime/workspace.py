"""Engineering workspace structure.

Each project workspace contains:
  - project.json       : project metadata
  - tasks.json         : task definitions and states
  - agents.json        : agent assignments
  - progress.json      : live progress
  - logs/              : execution logs
  - reports/           : generated reports
  - artifacts/         : agent outputs
  - generated/         : generated code
  - state/             : build state and diffs
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class EngineeringWorkspace:
    """Root object for an autonomous engineering project workspace."""

    root: str
    project_name: str = ""
    goal: str = ""
    status: str = "pending"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.root = os.path.normpath(self.root)
        self.project_name = self.project_name or os.path.basename(self.root)

    @property
    def project_json(self) -> str:
        return os.path.join(self.root, "project.json")

    @property
    def tasks_json(self) -> str:
        return os.path.join(self.root, "tasks.json")

    @property
    def agents_json(self) -> str:
        return os.path.join(self.root, "agents.json")

    @property
    def progress_json(self) -> str:
        return os.path.join(self.root, "progress.json")

    @property
    def logs_dir(self) -> str:
        return os.path.join(self.root, "logs")

    @property
    def reports_dir(self) -> str:
        return os.path.join(self.root, "reports")

    @property
    def artifacts_dir(self) -> str:
        return os.path.join(self.root, "artifacts")

    @property
    def generated_dir(self) -> str:
        return os.path.join(self.root, "generated")

    @property
    def state_dir(self) -> str:
        return os.path.join(self.root, "state")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "root": self.root,
            "project_name": self.project_name,
            "goal": self.goal,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EngineeringWorkspace:
        return cls(
            root=str(data.get("root", "")),
            project_name=str(data.get("project_name", "")),
            goal=str(data.get("goal", "")),
            status=str(data.get("status", "pending")),
            created_at=str(data.get("created_at", datetime.now(timezone.utc).isoformat())),
            updated_at=str(data.get("updated_at", datetime.now(timezone.utc).isoformat())),
            metadata=dict(data.get("metadata", {})),
        )

    def initialize(self) -> None:
        """Create the workspace directory structure."""
        os.makedirs(self.root, exist_ok=True)
        for path in (
            self.logs_dir,
            self.reports_dir,
            self.artifacts_dir,
            self.generated_dir,
            self.state_dir,
        ):
            os.makedirs(path, exist_ok=True)
        self._touch()

    def _touch(self):
        self.updated_at = datetime.now(timezone.utc).isoformat()
