"""Mission Control Telemetry Dashboard for live autonomous engineering observability."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional


class MissionControl:
    """Provides centralized live telemetry for running agents, queues, resources, and releases."""

    def __init__(self):
        self._active_project = "Idle"
        self._current_task = "None"
        self._agent_status = {
            "planner": "Healthy",
            "executor": "Idle",
            "qa": "Idle",
            "repair": "Idle",
            "reflection": "Healthy",
        }
        self._completed_tasks = 0
        self._failed_tasks = 0
        self._recovered_tasks = 0
        self._release_progress_pct = 0.0
        self._quality_score = 95.0

    def update_status(
        self,
        active_project: Optional[str] = None,
        current_task: Optional[str] = None,
        agent_status: Optional[Dict[str, str]] = None,
        completed_delta: int = 0,
        failed_delta: int = 0,
        recovered_delta: int = 0,
        release_progress_pct: Optional[float] = None,
        quality_score: Optional[float] = None,
    ):
        if active_project is not None:
            self._active_project = active_project
        if current_task is not None:
            self._current_task = current_task
        if agent_status:
            self._agent_status.update(agent_status)
        self._completed_tasks += completed_delta
        self._failed_tasks += failed_delta
        self._recovered_tasks += recovered_delta
        if release_progress_pct is not None:
            self._release_progress_pct = round(max(0.0, min(100.0, release_progress_pct)), 1)
        if quality_score is not None:
            self._quality_score = round(max(0.0, min(100.0, quality_score)), 1)

    def get_telemetry(self) -> Dict[str, Any]:
        return {
            "status": "🟢 Healthy",
            "active_project": self._active_project,
            "current_task": self._current_task,
            "agents": dict(self._agent_status),
            "tasks": {
                "completed": self._completed_tasks,
                "failed": self._failed_tasks,
                "recovered": self._recovered_tasks,
            },
            "release_progress_pct": self._release_progress_pct,
            "quality_score": self._quality_score,
            "timestamp": time.time(),
        }

    def render_cli_view(self) -> str:
        t = self.get_telemetry()
        bar_len = int(t["release_progress_pct"] / 10.0)
        progress_bar = "█" * bar_len + "░" * (10 - bar_len)
        return f"""──────────────────────────────────────────────
Jarvis-X Mission Control Telemetry
Status:            {t['status']}
Active Project:    {t['active_project']}
Current Task:      {t['current_task']}
Release Progress:  [{progress_bar}] {t['release_progress_pct']}%
Quality Score:     {t['quality_score']}%
Tasks:             {t['tasks']['completed']} completed | {t['tasks']['recovered']} recovered | {t['tasks']['failed']} failed
──────────────────────────────────────────────"""
