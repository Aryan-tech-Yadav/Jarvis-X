from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from app.core.logger import Logger
from config import WORKSPACE


class FileManager:
    """Manage project files safely within the configured workspace with atomic writes and rollback support."""

    def __init__(self, workspace=None):
        self.workspace = Path(workspace or WORKSPACE).expanduser().resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)

    def _workspace_path(self, filename: str | Path) -> Path:
        """Resolve a path and reject anything outside the workspace."""
        supplied = Path(filename).expanduser()
        candidate = (
            supplied if supplied.is_absolute()
            else self.workspace / supplied
        ).resolve()

        try:
            candidate.relative_to(self.workspace)
        except ValueError:
            raise ValueError("File path must remain inside the workspace")

        return candidate

    def _atomic_write(self, target_path: Path, content: str) -> None:
        """Atomically write content to file using tempfile + os.replace."""
        target_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = target_path.with_name(f".{target_path.name}.tmp.{os.getpid()}")
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp_path, target_path)
        except Exception:
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
            raise

    def save_python(self, filename: str | Path, code: str) -> str:
        path = self._workspace_path(filename)

        if not path.name:
            raise ValueError("A valid filename is required")

        self._atomic_write(path, code)
        Logger.success(f"Saved: {path}")
        return str(path)

    def create_snapshot(self, path: str | Path) -> str:
        """Create a backup snapshot before destructive operations."""
        target = self._workspace_path(path)
        if not target.is_file():
            raise FileNotFoundError(f"Cannot snapshot non-existent file: {target}")
        backup = target.with_suffix(target.suffix + ".bak")
        shutil.copy2(target, backup)
        Logger.info(f"Snapshot created: {backup}")
        return str(backup)

    def rollback(self, path: str | Path) -> bool:
        """Restore a file from its snapshot (.bak)."""
        target = self._workspace_path(path)
        backup = target.with_suffix(target.suffix + ".bak")
        if not backup.is_file():
            Logger.warning(f"No snapshot found to rollback: {backup}")
            return False
        os.replace(backup, target)
        Logger.success(f"Rolled back to snapshot: {target}")
        return True

    def open_in_vscode(self, path: str | Path):
        target = self._workspace_path(path)

        if not target.exists():
            raise FileNotFoundError(f"File or directory not found: {target}")

        vscode = shutil.which("code")
        if not vscode:
            raise FileNotFoundError(
                "VS Code command 'code' was not found. Install VS Code or add it to PATH."
            )

        Logger.info(f"Opening: {target}")
        return subprocess.Popen(
            [vscode, str(target)],
            shell=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def read_file(self, path: str | Path) -> str:
        target = self._workspace_path(path)
        if not target.is_file():
            raise FileNotFoundError(f"File not found: {target}")

        return target.read_text(encoding="utf-8")

    def overwrite_file(self, path: str | Path, code: str, create_backup: bool = True) -> str:
        target = self._workspace_path(path)
        if not target.is_file():
            raise FileNotFoundError(f"File not found: {target}")

        if create_backup:
            self.create_snapshot(target)

        self._atomic_write(target, code)
        Logger.success(f"Updated: {target}")
        return str(target)
