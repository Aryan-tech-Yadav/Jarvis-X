"""Execution monitor for autonomous engineering execution.

Tracks progress, collects metrics, and generates progress reports
during autonomous project execution.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.core.logger import Logger


@dataclass
class StageProgress:
    """Progress of a single execution stage."""

    stage_name: str
    status: str = "pending"  # pending, running, completed, failed
    start_time: float = 0.0
    end_time: float = 0.0
    message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "stage_name": self.stage_name,
            "status": self.status,
            "duration": round(self.end_time - self.start_time, 2) if self.start_time else 0.0,
            "message": self.message,
            "metadata": dict(self.metadata),
        }


@dataclass
class ExecutionProgress:
    """Overall execution progress tracker."""

    execution_id: str
    goal: str = ""
    current_stage: str = "start"
    overall_status: str = "running"  # running, completed, failed, paused
    start_time: float = 0.0
    end_time: float = 0.0
    stages: List[StageProgress] = field(default_factory=list)
    events: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "execution_id": self.execution_id,
            "goal": self.goal,
            "current_stage": self.current_stage,
            "overall_status": self.overall_status,
            "duration": round(self.end_time - self.start_time, 2) if self.start_time else 0.0,
            "stages": [s.to_dict() for s in self.stages],
            "events": list(self.events),
            "metrics": dict(self.metrics),
        }

    def summary(self) -> str:
        stage_names = [s.stage_name for s in self.stages]
        completed = sum(1 for s in self.stages if s.status == "completed")
        total = len(self.stages)
        return (
            f"Execution {self.execution_id}\n"
            f"Goal: {self.goal[:60]}{'...' if len(self.goal) > 60 else ''}\n"
            f"Status: {self.overall_status}\n"
            f"Progress: {completed}/{total} stages\n"
            f"Current: {self.current_stage}"
        )


class ExecutionMonitor:
    """Monitor autonomous execution progress.

    Tracks stage transitions, collects events, and computes
    real-time metrics.
    """

    def __init__(self):
        self._current: Optional[ExecutionProgress] = None
        self._stage_index: Dict[str, StageProgress] = {}

    def start(self, execution_id: str, goal: str) -> ExecutionProgress:
        """Start monitoring a new execution."""
        self._current = ExecutionProgress(
            execution_id=execution_id,
            goal=goal,
            start_time=time.perf_counter(),
        )
        self._stage_index = {}
        Logger.info(f"[ExecutionMonitor] Started monitoring {execution_id}")
        return self._current

    def stage_start(self, stage_name: str, metadata: Optional[Dict[str, Any]] = None):
        """Mark a stage as started."""
        if self._current is None:
            return

        if stage_name not in self._stage_index:
            stage = StageProgress(stage_name=stage_name, metadata=metadata or {})
            self._current.stages.append(stage)
            self._stage_index[stage_name] = stage

        stage = self._stage_index[stage_name]
        stage.status = "running"
        stage.start_time = time.perf_counter()
        self._current.current_stage = stage_name

        self._current.events.append({
            "type": "stage_start",
            "stage": stage_name,
            "timestamp": stage.start_time,
        })

        Logger.info(f"[ExecutionMonitor] Stage started: {stage_name}")

    def stage_complete(self, stage_name: str, message: str = "", metadata: Optional[Dict[str, Any]] = None):
        """Mark a stage as completed."""
        if self._current is None or stage_name not in self._stage_index:
            return

        stage = self._stage_index[stage_name]
        stage.status = "completed"
        stage.end_time = time.perf_counter()
        stage.message = message
        if metadata:
            stage.metadata.update(metadata)

        self._current.events.append({
            "type": "stage_complete",
            "stage": stage_name,
            "duration": stage.end_time - stage.start_time,
            "timestamp": stage.end_time,
        })

        Logger.success(f"[ExecutionMonitor] Stage completed: {stage_name} ({stage.end_time - stage.start_time:.2f}s)")

    def stage_fail(self, stage_name: str, error: str, metadata: Optional[Dict[str, Any]] = None):
        """Mark a stage as failed."""
        if self._current is None or stage_name not in self._stage_index:
            return

        stage = self._stage_index[stage_name]
        stage.status = "failed"
        stage.end_time = time.perf_counter()
        stage.message = error
        if metadata:
            stage.metadata.update(metadata)

        self._current.events.append({
            "type": "stage_fail",
            "stage": stage_name,
            "error": error,
            "timestamp": stage.end_time,
        })

        Logger.error(f"[ExecutionMonitor] Stage failed: {stage_name} - {error}")

    def update_metrics(self, metrics: Dict[str, Any]):
        """Update execution metrics."""
        if self._current is None:
            return
        self._current.metrics.update(metrics)

    def complete(self, success: bool, message: str = ""):
        """Mark execution as complete."""
        if self._current is None:
            return

        self._current.overall_status = "completed" if success else "failed"
        self._current.end_time = time.perf_counter()

        self._current.events.append({
            "type": "execution_complete",
            "success": success,
            "message": message,
            "duration": self._current.end_time - self._current.start_time,
            "timestamp": self._current.end_time,
        })

        status = "successfully" if success else "with failures"
        Logger.success(f"[ExecutionMonitor] Execution {self._current.execution_id} completed {status}")

    def get_progress(self) -> Optional[ExecutionProgress]:
        """Get current progress."""
        return self._current

    def get_summary(self) -> str:
        """Get human-readable summary."""
        if self._current is None:
            return "No active execution"
        return self._current.summary()
