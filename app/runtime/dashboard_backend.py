"""Dashboard Backend - Generate status.json for dashboard.

Provides runtime status information for the dashboard to consume.
Generates status.json file with current system state.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.logger import Logger


class DashboardBackend:
    """Generate dashboard status data.

    Generates status.json with:
      - Running tasks
      - Completed projects
      - Repair rate
      - Test coverage
      - System health
      - Memory usage
      - Knowledge base size
    """

    def __init__(self, output_dir: str = "data/dashboard"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.status_file = self.output_dir / "status.json"

    def generate_status(self, context: Any = None) -> Dict[str, Any]:
        """Generate status dictionary.

        Args:
            context: Optional runtime context

        Returns:
            Status dictionary
        """
        status = {
            "timestamp": datetime.now().isoformat(),
            "running_tasks": self._count_running_tasks(context),
            "completed_projects": self._count_completed_projects(),
            "repair_rate": self._calculate_repair_rate(),
            "coverage": self._get_coverage(),
            "health": self._get_health_status(),
            "memory": self._get_memory_usage(),
            "knowledge": self._get_knowledge_size(),
            "uptime": self._get_uptime(),
        }

        return status

    def write_status(self, context: Any = None) -> Path:
        """Generate and write status.json.

        Args:
            context: Optional runtime context

        Returns:
            Path to status.json
        """
        status = self.generate_status(context)
        with open(self.status_file, "w", encoding="utf-8") as f:
            json.dump(status, f, indent=2)
        Logger.info(f"[Dashboard] Status written to {self.status_file}")
        return self.status_file

    def get_status(self, context: Any = None) -> Dict[str, Any]:
        """Get current status, reading from file if available.

        Args:
            context: Optional runtime context

        Returns:
            Status dictionary
        """
        if self.status_file.exists():
            try:
                with open(self.status_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return self.generate_status(context)

    def _count_running_tasks(self, context: Any = None) -> int:
        """Count currently running tasks."""
        if context and hasattr(context, 'current_task'):
            task = context.current_task
            if hasattr(task, 'status') and task.status in ("running", "planning", "coding", "testing"):
                return 1
        return 0

    def _count_completed_projects(self) -> int:
        """Count completed projects."""
        try:
            workspace = Path("workspace")
            if not workspace.exists():
                return 0
            return len([d for d in workspace.iterdir() if d.is_dir()])
        except Exception:
            return 0

    def _calculate_repair_rate(self) -> int:
        """Calculate repair success rate (0-100)."""
        try:
            repair_log = Path("data/repairs")
            if not repair_log.exists():
                return 100
            total = 0
            successful = 0
            for filepath in repair_log.glob("*.json"):
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if data.get("success") == "YES":
                            successful += 1
                        total += 1
                except Exception:
                    pass
            return int((successful / max(1, total)) * 100)
        except Exception:
            return 100

    def _get_coverage(self) -> int:
        """Get test coverage percentage."""
        try:
            metrics_file = Path("data/metrics.json")
            if metrics_file.exists():
                with open(metrics_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("coverage", 0)
            return 0
        except Exception:
            return 0

    def _get_health_status(self) -> str:
        """Get system health status."""
        try:
            # Check critical components
            issues = []

            # Check workspace
            if not Path("workspace").exists():
                issues.append("workspace_missing")

            # Check data directories
            for dir_name in ["data", "data/knowledge", "data/reflections"]:
                if not Path(dir_name).exists():
                    issues.append(f"{dir_name}_missing")

            if issues:
                return f"Degraded ({len(issues)} issues)"
            return "Healthy"
        except Exception:
            return "Unknown"

    def _get_memory_usage(self) -> int:
        """Get memory usage in MB."""
        try:
            import psutil
            process = psutil.Process()
            return int(process.memory_info().rss / 1024 / 1024)
        except ImportError:
            # Fallback: estimate from context
            return 0
        except Exception:
            return 0

    def _get_knowledge_size(self) -> int:
        """Get knowledge base size."""
        try:
            knowledge_dir = Path("data/knowledge")
            if not knowledge_dir.exists():
                return 0
            count = 0
            for filepath in knowledge_dir.glob("*.json"):
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        count += len(data) if isinstance(data, dict) else 0
                except Exception:
                    pass
            return count
        except Exception:
            return 0

    def _get_uptime(self) -> int:
        """Get system uptime in seconds."""
        try:
            import time
            return int(time.time() - Path("data").stat().st_mtime)
        except Exception:
            return 0
