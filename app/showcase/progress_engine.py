"""Live Progress Engine for real-time visual pipeline step tracking."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class StageProgress:
    name: str
    percent: float = 0.0
    status: str = "WAITING"  # WAITING, RUNNING, COMPLETED, FAILED
    message: str = ""

    def render_bar(self, width: int = 15) -> str:
        filled = int((self.percent / 100.0) * width)
        bar = "█" * filled + "░" * (width - filled)
        return f"{self.name:<12} [{bar}] {self.percent:>5.1f}% ({self.status})"


class LiveProgressEngine:
    """Tracks and renders live multi-stage execution progress across the entire pipeline."""

    STAGE_NAMES = ["Planner", "Executor", "Testing", "Repair", "Packaging"]

    def __init__(self):
        self.stages: Dict[str, StageProgress] = {
            name: StageProgress(name=name) for name in self.STAGE_NAMES
        }
        self.start_time = time.perf_counter()

    def update_stage(self, name: str, percent: float, status: str = "RUNNING", message: str = ""):
        if name in self.stages:
            self.stages[name].percent = round(max(0.0, min(100.0, percent)), 1)
            self.stages[name].status = status
            self.stages[name].message = message

    def complete_all(self):
        for s in self.stages.values():
            s.percent = 100.0
            s.status = "COMPLETED"

    def render_progress_view(self) -> str:
        lines = [
            "──────────────────────────────────────────────",
            "🚀 Jarvis-X Autonomous Generation Pipeline",
            "──────────────────────────────────────────────",
        ]
        for s in self.stages.values():
            lines.append(s.render_bar())
        lines.append("──────────────────────────────────────────────")
        return "\n".join(lines)
