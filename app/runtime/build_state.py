"""Build state for incremental project generation.

Tracks which files exist, their versions, and whether they need
regeneration. This enables incremental builds instead of full rebuilds.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class FileState:
    """State of a single generated file."""

    path: str
    checksum: str = ""
    size_bytes: int = 0
    generated_by: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    version: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "checksum": self.checksum,
            "size_bytes": self.size_bytes,
            "generated_by": self.generated_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FileState:
        return cls(
            path=str(data.get("path", "")),
            checksum=str(data.get("checksum", "")),
            size_bytes=int(data.get("size_bytes", 0)),
            generated_by=str(data.get("generated_by", "")),
            created_at=str(data.get("created_at", "")),
            updated_at=str(data.get("updated_at", "")),
            version=int(data.get("version", 1)),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass
class BuildState:
    """Persistent state for incremental builds."""

    project_name: str = ""
    project_path: str = ""
    files: Dict[str, FileState] = field(default_factory=dict)
    last_build_goal: str = ""
    last_build_at: str = ""
    build_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "project_path": self.project_path,
            "files": {path: fs.to_dict() for path, fs in self.files.items()},
            "last_build_goal": self.last_build_goal,
            "last_build_at": self.last_build_at,
            "build_count": self.build_count,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BuildState:
        files = {}
        for path, fs_data in data.get("files", {}).items():
            files[path] = FileState.from_dict(fs_data)
        return cls(
            project_name=str(data.get("project_name", "")),
            project_path=str(data.get("project_path", "")),
            files=files,
            last_build_goal=str(data.get("last_build_goal", "")),
            last_build_at=str(data.get("last_build_at", "")),
            build_count=int(data.get("build_count", 0)),
            metadata=dict(data.get("metadata", {})),
        )


class BuildStateManager:
    """Manage incremental build state."""

    def __init__(self, state_path: str = os.path.join("state", "build_state.json")):
        self.state_path = state_path
        self.state = BuildState()
        self._load()

    def _load(self):
        if os.path.isfile(self.state_path):
            try:
                with open(self.state_path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                self.state = BuildState.from_dict(raw)
            except (OSError, json.JSONDecodeError, TypeError):
                pass

    def _save(self):
        os.makedirs(os.path.dirname(self.state_path) or ".", exist_ok=True)
        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump(self.state.to_dict(), f, indent=2, default=str)

    def record_file(self, file_path: str, content: str, generated_by: str = ""):
        """Record a generated file's state."""
        checksum = hashlib.sha256(content.encode("utf-8", errors="replace")).hexdigest()[:16]
        size_bytes = len(content.encode("utf-8", errors="replace"))
        
        if file_path in self.state.files:
            existing = self.state.files[file_path]
            if existing.checksum == checksum:
                return False  # No change
            existing.checksum = checksum
            existing.size_bytes = size_bytes
            existing.updated_at = datetime.now(timezone.utc).isoformat()
            existing.version += 1
            existing.generated_by = generated_by
        else:
            self.state.files[file_path] = FileState(
                path=file_path,
                checksum=checksum,
                size_bytes=size_bytes,
                generated_by=generated_by,
            )
        self._save()
        return True

    def record_build(self, goal: str):
        self.state.last_build_goal = goal
        self.state.last_build_at = datetime.now(timezone.utc).isoformat()
        self.state.build_count += 1
        self._save()

    def needs_regeneration(self, file_path: str, new_content: str) -> bool:
        """Check if a file needs regeneration based on content hash."""
        checksum = hashlib.sha256(new_content.encode("utf-8", errors="replace")).hexdigest()[:16]
        existing = self.state.files.get(file_path)
        if not existing:
            return True
        return existing.checksum != checksum

    def get_changed_files(self, current_files: Dict[str, str]) -> List[str]:
        """Return list of files that have changed since last build."""
        changed = []
        for file_path, content in current_files.items():
            if self.needs_regeneration(file_path, content):
                changed.append(file_path)
        return changed

    def get_new_files(self, current_files: Dict[str, str]) -> List[str]:
        """Return list of files that don't exist in current build state."""
        return [path for path in current_files if path not in self.state.files]

    def get_deleted_files(self, current_files: Dict[str, str]) -> List[str]:
        """Return list of files that were in build state but are no longer present."""
        return [path for path in self.state.files if path not in current_files]
