"""Version manager for self-improvement.

Manages project versions, snapshots, and activation.
"""

from __future__ import annotations

import json
import os
import shutil
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class ProjectVersion:
    """Single project version snapshot."""

    version_id: str
    version_name: str
    project_path: str
    snapshot_path: str
    score: float = 0.0
    status: str = "inactive"  # active, inactive, archived
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version_id": self.version_id,
            "version_name": self.version_name,
            "project_path": self.project_path,
            "snapshot_path": self.snapshot_path,
            "score": round(self.score, 2),
            "status": self.status,
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }


class VersionManager:
    """Manage project versions and snapshots."""

    def __init__(self, versions_root: str = ".versions"):
        self.versions_root = versions_root
        self._versions: Dict[str, ProjectVersion] = {}
        self._active_version: Optional[str] = None
        os.makedirs(versions_root, exist_ok=True)

    def create_version(self, project_path: str, version_name: str = "", score: float = 0.0) -> ProjectVersion:
        """Create a new version snapshot."""
        version_id = f"ver-{uuid.uuid4().hex[:12]}"
        version_name = version_name or f"version-{len(self._versions) + 1}"
        snapshot_path = os.path.join(self.versions_root, version_id)

        # Clone project
        if os.path.isdir(project_path):
            shutil.copytree(
                project_path,
                snapshot_path,
                ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc", ".pytest_cache", "*.egg-info"),
            )
        else:
            os.makedirs(snapshot_path, exist_ok=True)

        version = ProjectVersion(
            version_id=version_id,
            version_name=version_name,
            project_path=os.path.abspath(project_path),
            snapshot_path=os.path.abspath(snapshot_path),
            score=score,
        )
        self._versions[version_id] = version
        self._active_version = version_id
        return version

    def get_version(self, version_id: str) -> Optional[ProjectVersion]:
        """Get version by ID."""
        return self._versions.get(version_id)

    def list_versions(self) -> List[Dict[str, Any]]:
        """List all versions."""
        return [v.to_dict() for v in self._versions.values()]

    def activate(self, version_id: str) -> bool:
        """Activate a specific version."""
        version = self._versions.get(version_id)
        if not version or not os.path.isdir(version.snapshot_path):
            return False

        # Deactivate current
        if self._active_version and self._active_version in self._versions:
            self._versions[self._active_version].status = "inactive"

        # Restore snapshot to project path
        try:
            if os.path.exists(version.project_path):
                shutil.rmtree(version.project_path)
            shutil.copytree(version.snapshot_path, version.project_path)
            version.status = "active"
            self._active_version = version_id
            return True
        except (OSError, shutil.Error):
            return False

    def archive(self, version_id: str) -> bool:
        """Archive a version."""
        version = self._versions.get(version_id)
        if not version:
            return False
        version.status = "archived"
        return True

    def delete(self, version_id: str) -> bool:
        """Delete a version snapshot."""
        version = self._versions.get(version_id)
        if not version:
            return False
        try:
            if os.path.isdir(version.snapshot_path):
                shutil.rmtree(version.snapshot_path)
            del self._versions[version_id]
            if self._active_version == version_id:
                self._active_version = None
            return True
        except (OSError, shutil.Error):
            return False

    def get_active_version(self) -> Optional[ProjectVersion]:
        """Get the currently active version."""
        if self._active_version:
            return self._versions.get(self._active_version)
        return None

    def get_latest_version(self) -> Optional[ProjectVersion]:
        """Get the most recent version."""
        if not self._versions:
            return None
        # Use insertion order as tiebreaker when timestamps collide
        return max(self._versions.values(), key=lambda v: (v.created_at, list(self._versions.values()).index(v)))
