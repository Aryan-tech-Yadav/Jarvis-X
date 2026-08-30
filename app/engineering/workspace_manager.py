"""Engineering workspace manager.

Manages multiple isolated project workspaces. Each project gets its own
directory and metadata, and the manager can switch context automatically.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.core.logger import Logger
from app.core.results import ExecutionResult


@dataclass
class WorkspaceProject:
    """Metadata for a single managed project."""

    name: str
    path: str
    goal: str = ""
    status: str = "created"
    success: bool = False
    overall_score: float = 0.0
    artifacts: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path,
            "goal": self.goal,
            "status": self.status,
            "success": self.success,
            "overall_score": round(self.overall_score, 2),
            "artifacts": list(self.artifacts),
        }


class WorkspaceManager:
    """Manage multiple isolated engineering project workspaces."""

    def __init__(self, workspace_root: str = "workspace", metadata_file: str = os.path.join("data", "workspace_metadata.json")):
        self.workspace_root = workspace_root
        self.metadata_file = metadata_file
        self._projects: Dict[str, WorkspaceProject] = {}
        self._active_project: Optional[str] = None
        self._load_metadata()

    def _load_metadata(self):
        if os.path.isfile(self.metadata_file):
            try:
                with open(self.metadata_file, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                if isinstance(raw, dict):
                    for name, data in raw.items():
                        if isinstance(data, dict):
                            self._projects[name] = WorkspaceProject(
                                name=name,
                                path=data.get("path", os.path.join(self.workspace_root, name)),
                                goal=data.get("goal", ""),
                                status=data.get("status", "created"),
                                success=data.get("success", False),
                                overall_score=data.get("overall_score", 0.0),
                                artifacts=data.get("artifacts", []),
                            )
            except (OSError, json.JSONDecodeError, TypeError):
                pass

    def _save_metadata(self):
        os.makedirs(os.path.dirname(self.metadata_file), exist_ok=True)
        payload = {name: proj.to_dict() for name, proj in self._projects.items()}
        with open(self.metadata_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    def create_project(self, name: str, goal: str = "") -> ExecutionResult:
        if not isinstance(name, str) or not name.strip():
            return ExecutionResult.failed("Project name cannot be empty")

        name = name.strip().replace(" ", "_").lower()
        project_path = os.path.join(self.workspace_root, name)

        if os.path.exists(project_path):
            import shutil
            shutil.rmtree(project_path)
            Logger.warning(f"[WorkspaceManager] Removed existing project: {project_path}")

        try:
            os.makedirs(project_path, exist_ok=True)
            project = WorkspaceProject(name=name, path=project_path, goal=goal, status="created")
            self._projects[name] = project
            self._active_project = name
            self._save_metadata()
            Logger.success(f"[WorkspaceManager] Created project: {project_path}")
            return ExecutionResult.completed(
                data=project.to_dict(),
                message="Project workspace created",
                artifacts=[project_path],
            )
        except Exception as exc:
            Logger.error(f"Failed to create workspace project: {exc}")
            return ExecutionResult.failed(str(exc))

    def get_project(self, name: str) -> Optional[WorkspaceProject]:
        return self._projects.get(name)

    def get_active_project(self) -> Optional[WorkspaceProject]:
        if self._active_project:
            return self._projects.get(self._active_project)
        return None

    def switch_project(self, name: str) -> ExecutionResult:
        project = self._projects.get(name)
        if not project:
            return ExecutionResult.failed(f"Project not found: {name}")
        self._active_project = name
        Logger.info(f"[WorkspaceManager] Switched to project: {name}")
        return ExecutionResult.completed(data=project.to_dict(), message=f"Switched to {name}")

    def update_project(self, name: str, **updates) -> ExecutionResult:
        project = self._projects.get(name)
        if not project:
            return ExecutionResult.failed(f"Project not found: {name}")

        for key, value in updates.items():
            if hasattr(project, key):
                setattr(project, key, value)

        self._save_metadata()
        return ExecutionResult.completed(data=project.to_dict(), message="Project updated")

    def list_projects(self) -> List[Dict[str, Any]]:
        return [proj.to_dict() for proj in self._projects.values()]

    def delete_project(self, name: str) -> ExecutionResult:
        project = self._projects.get(name)
        if not project:
            return ExecutionResult.failed(f"Project not found: {name}")

        try:
            import shutil
            if os.path.isdir(project.path):
                shutil.rmtree(project.path)
            del self._projects[name]
            if self._active_project == name:
                self._active_project = None
            self._save_metadata()
            return ExecutionResult.completed(message=f"Deleted project: {name}")
        except Exception as exc:
            return ExecutionResult.failed(str(exc))
