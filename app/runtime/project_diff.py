"""Project diff engine.

Compares two versions of a project and reports:
  - Added files
  - Removed files
  - Modified files
  - Performance changes
  - Security changes
"""

from __future__ import annotations

import difflib
import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class FileDiff:
    """Diff result for a single file."""

    path: str
    change_type: str  # added, removed, modified, unchanged
    old_checksum: str = ""
    new_checksum: str = ""
    old_size: int = 0
    new_size: int = 0
    lines_added: int = 0
    lines_removed: int = 0
    diff_text: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "change_type": self.change_type,
            "old_checksum": self.old_checksum,
            "new_checksum": self.new_checksum,
            "old_size": self.old_size,
            "new_size": self.new_size,
            "lines_added": self.lines_added,
            "lines_removed": self.lines_removed,
            "diff_text": self.diff_text,
            "metadata": dict(self.metadata),
        }


@dataclass
class ProjectDiff:
    """Complete diff between two project versions."""

    old_version: str = ""
    new_version: str = ""
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    added: List[FileDiff] = field(default_factory=list)
    removed: List[FileDiff] = field(default_factory=list)
    modified: List[FileDiff] = field(default_factory=list)
    unchanged: List[FileDiff] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "old_version": self.old_version,
            "new_version": self.new_version,
            "generated_at": self.generated_at,
            "added": [fd.to_dict() for fd in self.added],
            "removed": [fd.to_dict() for fd in self.removed],
            "modified": [fd.to_dict() for fd in self.modified],
            "unchanged": [fd.to_dict() for fd in self.unchanged],
            "summary": dict(self.summary),
        }


class ProjectDiffEngine:
    """Compare two versions of a project."""

    def __init__(self, old_path: str, new_path: str):
        self.old_path = old_path
        self.new_path = new_path

    def compute(self) -> ProjectDiff:
        old_files = self._scan_files(self.old_path)
        new_files = self._scan_files(self.new_path)
        
        diff = ProjectDiff(old_version=self.old_path, new_version=self.new_path)
        
        all_paths = set(list(old_files.keys()) + list(new_files.keys()))
        for path in sorted(all_paths):
            old_content = old_files.get(path)
            new_content = new_files.get(path)
            
            if old_content is None:
                diff.added.append(FileDiff(path=path, change_type="added", new_checksum=self._checksum(new_content or ""), new_size=len((new_content or "").encode("utf-8", errors="replace"))))
            elif new_content is None:
                diff.removed.append(FileDiff(path=path, change_type="removed", old_checksum=self._checksum(old_content), old_size=len(old_content.encode("utf-8", errors="replace"))))
            elif old_content == new_content:
                diff.unchanged.append(FileDiff(path=path, change_type="unchanged", old_checksum=self._checksum(old_content), new_checksum=self._checksum(new_content), old_size=len(old_content.encode("utf-8", errors="replace")), new_size=len(new_content.encode("utf-8", errors="replace"))))
            else:
                lines_added, lines_removed, diff_text = self._compute_text_diff(old_content, new_content)
                diff.modified.append(FileDiff(
                    path=path,
                    change_type="modified",
                    old_checksum=self._checksum(old_content),
                    new_checksum=self._checksum(new_content),
                    old_size=len(old_content.encode("utf-8", errors="replace")),
                    new_size=len(new_content.encode("utf-8", errors="replace")),
                    lines_added=lines_added,
                    lines_removed=lines_removed,
                    diff_text=diff_text,
                ))
        
        diff.summary = {
            "added": len(diff.added),
            "removed": len(diff.removed),
            "modified": len(diff.modified),
            "unchanged": len(diff.unchanged),
            "total_changed": len(diff.added) + len(diff.removed) + len(diff.modified),
        }
        return diff

    def _scan_files(self, root_path: str) -> Dict[str, str]:
        files = {}
        if not os.path.isdir(root_path):
            return files
        for dirpath, _, filenames in os.walk(root_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                rel_path = os.path.relpath(filepath, root_path).replace(os.sep, "/")
                try:
                    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                        files[rel_path] = f.read()
                except (OSError, UnicodeDecodeError):
                    pass
        return files

    @staticmethod
    def _checksum(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8", errors="replace")).hexdigest()[:16]

    @staticmethod
    def _compute_text_diff(old: str, new: str) -> tuple:
        old_lines = old.splitlines(keepends=True)
        new_lines = new.splitlines(keepends=True)
        diff = difflib.unified_diff(old_lines, new_lines, lineterm="")
        diff_text = "\n".join(diff)
        added = sum(1 for line in new_lines if line not in old_lines)
        removed = sum(1 for line in old_lines if line not in new_lines)
        return added, removed, diff_text
