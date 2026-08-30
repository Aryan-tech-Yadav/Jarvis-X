"""File scanner for project analysis.

Discovers Python files in a project directory while respecting
ignore rules for virtual environments, cache directories, and
build artifacts.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Set


class ScannerError(Exception):
    """Base scanner error."""


class InvalidPathError(ScannerError):
    """Raised when project path is invalid."""


@dataclass
class FileScannerResult:
    """Result of file scanning operation."""

    root: str
    python_files: List[str] = field(default_factory=list)
    ignored_dirs: Set[str] = field(default_factory=lambda: {
        ".git", ".venv", "venv", "__pycache__", ".pytest_cache",
        "node_modules", "dist", "build", "workspace", ".sandboxes",
        ".mypy_cache", ".ruff_cache", ".tox", ".eggs", "*.egg-info",
    })
    total_files: int = 0
    scanned_dirs: int = 0

    def to_dict(self) -> dict:
        return {
            "root": self.root,
            "python_files": list(self.python_files),
            "ignored_dirs": list(self.ignored_dirs),
            "total_files": self.total_files,
            "scanned_dirs": self.scanned_dirs,
        }


class FileScanner:
    """Discover Python files in a project directory.

    Respects ignore rules and returns relative paths for all
    discovered Python source files.
    """

    def __init__(self, root: str | Path, ignored_dirs: Set[str] | None = None):
        self.root = Path(root).resolve()
        if not self.root.is_dir():
            raise InvalidPathError(f"Project root is not a directory: {self.root}")
        self.ignored_dirs = ignored_dirs or {
            ".git", ".venv", "venv", "__pycache__", ".pytest_cache",
            "node_modules", "dist", "build", "workspace", ".sandboxes",
            ".mypy_cache", ".ruff_cache", ".tox", ".eggs",
        }

    def scan(self) -> FileScannerResult:
        """Scan project directory for Python files.

        Returns:
            FileScannerResult with discovered Python files.
        """
        result = FileScannerResult(root=str(self.root))
        self._walk(self.root, result)
        result.total_files = len(result.python_files)
        return result

    def _walk(self, directory: Path, result: FileScannerResult):
        """Recursively walk directory collecting Python files."""
        try:
            entries = sorted(directory.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        except (OSError, PermissionError):
            return

        dirs: List[Path] = []
        for entry in entries:
            if entry.is_dir():
                name = entry.name
                if name in self.ignored_dirs or name.startswith("."):
                    continue
                dirs.append(entry)
            elif entry.is_file() and entry.suffix == ".py":
                rel_path = entry.relative_to(self.root)
                result.python_files.append(str(rel_path).replace("\\", "/"))

        for d in dirs:
            result.scanned_dirs += 1
            self._walk(d, result)
