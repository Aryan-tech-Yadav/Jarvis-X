"""Scheduler for multi-agent execution.

Schedules tasks from the task graph, manages execution order,
and tracks progress through phases.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ScheduledTask:
    """A task scheduled for execution."""

    task_id: str
    agent: str
    priority: str = "medium"
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "agent": self.agent,
            "priority": self.priority,
            "status": self.status,
            "result": self.result,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error": self.error,
        }


@dataclass
class ExecutionSchedule:
    """Complete execution schedule."""

    phases: List[List[ScheduledTask]] = field(default_factory=list)
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration: float = 0.0

    def to_dict(self) -> dict:
        return {
            "phases": [[t.to_dict() for t in phase] for phase in self.phases],
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": round(self.duration, 2),
        }


class TaskScheduler:
    """Schedule tasks for execution.

    Takes a task graph and creates an execution schedule
    with parallel groups and phase definitions.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._running = False

    def schedule(self, task_graph) -> ExecutionSchedule:
        """Create execution schedule from task graph.

        Args:
            task_graph: TaskGraph with all tasks.

        Returns:
            ExecutionSchedule with ordered phases.
        """
        parallel_groups = task_graph.get_parallel_groups()
        phases = []

        for group in parallel_groups:
            phase_tasks = []
            for task_id in group:
                task = task_graph.get_task(task_id)
                if task:
                    phase_tasks.append(ScheduledTask(
                        task_id=task.id,
                        agent=task.agent,
                        priority=task.priority,
                    ))
            if phase_tasks:
                phases.append(phase_tasks)

        schedule = ExecutionSchedule(
            phases=phases,
            total_tasks=len(task_graph._nodes),
        )
        return schedule

    def execute(self, schedule: ExecutionSchedule, executor: Callable[[ScheduledTask], Dict[str, Any]]) -> ExecutionSchedule:
        """Execute a schedule using the provided executor function.

        Args:
            schedule: ExecutionSchedule to execute.
            executor: Callable that takes a ScheduledTask and returns result dict.

        Returns:
            Updated ExecutionSchedule with results.
        """
        schedule.start_time = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
        started = time.perf_counter()
        self._running = True

        try:
            for phase in schedule.phases:
                if not self._running:
                    break

                # Execute phase tasks
                for task in phase:
                    if not self._running:
                        break

                    task.status = "running"
                    task.started_at = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())

                    try:
                        result = executor(task)
                        task.result = result
                        task.status = "completed" if result.get("success", False) else "failed"
                        if not result.get("success", False):
                            task.error = result.get("error", result.get("output", "Unknown error"))
                            schedule.failed_tasks += 1
                        else:
                            schedule.completed_tasks += 1
                    except Exception as exc:
                        task.status = "failed"
                        task.error = str(exc)
                        schedule.failed_tasks += 1

                    task.completed_at = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())

        finally:
            self._running = False
            schedule.end_time = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
            schedule.duration = time.perf_counter() - started

        return schedule

    def stop(self):
        """Stop execution."""
        self._running = False

    @property
    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._running
