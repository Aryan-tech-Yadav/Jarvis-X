"""State backup, recovery drills, and operational metrics monitoring."""

from __future__ import annotations

import json
import os
import shutil
import tarfile
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class OperationalMetrics:
    """Tracks runtime reliability metrics."""

    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    retried_tasks: int = 0
    timeout_tasks: int = 0
    unhandled_exceptions: int = 0
    latencies: List[float] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if self.total_tasks == 0:
            return 100.0
        return round((self.successful_tasks / self.total_tasks) * 100.0, 2)

    @property
    def failure_rate(self) -> float:
        if self.total_tasks == 0:
            return 0.0
        return round((self.failed_tasks / self.total_tasks) * 100.0, 2)

    @property
    def retry_rate(self) -> float:
        if self.total_tasks == 0:
            return 0.0
        return round((self.retried_tasks / self.total_tasks) * 100.0, 2)

    @property
    def avg_latency_sec(self) -> float:
        if not self.latencies:
            return 0.0
        return round(sum(self.latencies) / len(self.latencies), 3)

    def record_task(
        self,
        success: bool,
        duration_sec: float = 0.0,
        retried: bool = False,
        timed_out: bool = False,
        unhandled: bool = False,
    ):
        self.total_tasks += 1
        if success:
            self.successful_tasks += 1
        else:
            self.failed_tasks += 1

        if retried:
            self.retried_tasks += 1
        if timed_out:
            self.timeout_tasks += 1
        if unhandled:
            self.unhandled_exceptions += 1

        if duration_sec > 0:
            self.latencies.append(duration_sec)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_tasks": self.total_tasks,
            "successful_tasks": self.successful_tasks,
            "failed_tasks": self.failed_tasks,
            "retried_tasks": self.retried_tasks,
            "timeout_tasks": self.timeout_tasks,
            "unhandled_exceptions": self.unhandled_exceptions,
            "success_rate": self.success_rate,
            "failure_rate": self.failure_rate,
            "retry_rate": self.retry_rate,
            "avg_latency_sec": self.avg_latency_sec,
        }


class BackupManager:
    """Versioned state backups and automated restore drills."""

    def __init__(self, backup_dir: str | Path = "backups"):
        self.backup_dir = Path(backup_dir).resolve()
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, source_dir: str | Path, tag: str = "state") -> Path:
        """Create a compressed tar.gz snapshot of the source directory."""
        source = Path(source_dir).resolve()
        if not source.exists():
            raise FileNotFoundError(f"Source directory does not exist: {source}")

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"backup_{tag}_{timestamp}.tar.gz"

        with tarfile.open(backup_file, "w:gz") as tar:
            tar.add(source, arcname=source.name)

        return backup_file

    def restore_backup(self, backup_file: str | Path, target_dir: str | Path) -> bool:
        """Restore an archive safely into target_dir."""
        backup_path = Path(backup_file).resolve()
        target = Path(target_dir).resolve()

        if not backup_path.is_file():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")

        target.mkdir(parents=True, exist_ok=True)

        with tarfile.open(backup_path, "r:gz") as tar:
            # Prevent path traversal in tar extraction
            for member in tar.getmembers():
                dest_path = (target / member.name).resolve()
                if not dest_path.is_relative_to(target):
                    raise PermissionError(f"Attempted path traversal in archive: {member.name}")
            tar.extractall(target)

        return True

    def test_restore_drill(self, source_dir: str | Path) -> Dict[str, Any]:
        """Perform a non-destructive backup-and-restore drill into a temporary location."""
        import tempfile

        started = time.perf_counter()
        source = Path(source_dir).resolve()

        if not source.exists():
            return {"success": False, "error": f"Source directory {source} does not exist"}

        with tempfile.TemporaryDirectory() as drill_tmp:
            try:
                # 1. Create backup
                backup_path = self.create_backup(source, tag="drill")

                # 2. Extract into drill target
                drill_target = Path(drill_tmp) / "restored"
                drill_target.mkdir(parents=True, exist_ok=True)
                self.restore_backup(backup_path, drill_target)

                # 3. Verify integrity
                restored_root = drill_target / source.name
                original_files = set(
                    p.relative_to(source) for p in source.rglob("*") if p.is_file()
                )
                restored_files = set(
                    p.relative_to(restored_root) for p in restored_root.rglob("*") if p.is_file()
                )

                missing = original_files - restored_files
                success = len(missing) == 0

                # Clean up drill archive
                if backup_path.exists():
                    backup_path.unlink()

                return {
                    "success": success,
                    "duration_sec": round(time.perf_counter() - started, 3),
                    "files_checked": len(original_files),
                    "missing_files": [str(m) for m in missing],
                }
            except Exception as exc:
                return {
                    "success": False,
                    "duration_sec": round(time.perf_counter() - started, 3),
                    "error": str(exc),
                }

