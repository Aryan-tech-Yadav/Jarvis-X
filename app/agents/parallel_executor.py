"""Parallel agent executor for scalable multi-agent orchestration.

Executes independent agents concurrently using thread pools,
while respecting dependency ordering for dependent tasks.
"""

from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from app.core.logger import Logger


@dataclass
class AgentTask:
    """A single agent execution task."""

    agent_name: str
    task: Any
    dependencies: List[str] = field(default_factory=list)
    retries: int = 0
    timeout: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "agent_name": self.agent_name,
            "dependencies": list(self.dependencies),
            "retries": self.retries,
            "timeout": self.timeout,
            "metadata": dict(self.metadata),
        }


@dataclass
class AgentResult:
    """Result of a single agent execution."""

    agent_name: str
    success: bool
    output: Any = None
    error: Optional[str] = None
    duration: float = 0.0
    attempts: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "agent_name": self.agent_name,
            "success": self.success,
            "output": str(self.output)[:200] if self.output else None,
            "error": self.error,
            "duration": round(self.duration, 2),
            "attempts": self.attempts,
            "metadata": dict(self.metadata),
        }


class ParallelAgentExecutor:
    """Execute agent tasks in parallel with dependency resolution.

    Features:
      - Thread-based parallel execution
      - Dependency-aware scheduling
      - Retry with backoff
      - Timeout support
      - Result aggregation
    """

    def __init__(
        self,
        max_workers: int = 4,
        default_retries: int = 1,
        default_timeout: Optional[float] = None,
    ):
        self.max_workers = max_workers
        self.default_retries = default_retries
        self.default_timeout = default_timeout
        self._results: Dict[str, AgentResult] = {}
        self._lock = threading.Lock()

    def execute(
        self,
        tasks: List[AgentTask],
        executor: Callable[[AgentTask], AgentResult],
    ) -> List[AgentResult]:
        """Execute agent tasks in parallel.

        Args:
            tasks: List of AgentTask objects with dependencies.
            executor: Callable that executes a single AgentTask and returns AgentResult.

        Returns:
            List of AgentResult objects.
        """
        if not tasks:
            return []

        self._results = {}
        completed: Set[str] = set()
        failed: Set[str] = set()
        remaining = {t.agent_name: t for t in tasks}

        Logger.info(f"[ParallelExecutor] Starting execution of {len(tasks)} tasks with {self.max_workers} workers")

        while remaining:
            # Find tasks whose dependencies are satisfied
            ready = [
                task for task in remaining.values()
                if all(dep in completed or dep in failed for dep in task.dependencies)
            ]

            if not ready:
                # Circular dependency or all remaining tasks are blocked
                blocked = [name for name, task in remaining.items()]
                Logger.warning(f"[ParallelExecutor] Blocked tasks: {blocked}")
                break

            # Execute ready tasks in parallel
            batch_results = self._execute_batch(ready, executor)

            for result in batch_results:
                self._results[result.agent_name] = result
                if result.success:
                    completed.add(result.agent_name)
                else:
                    failed.add(result.agent_name)

            # Remove completed/failed tasks from remaining
            for name in list(remaining.keys()):
                if name in completed or name in failed:
                    del remaining[name]

        Logger.info(f"[ParallelExecutor] Completed: {len(completed)}, Failed: {len(failed)}")
        return list(self._results.values())

    def _execute_batch(self, tasks: List[AgentTask], executor: Callable) -> List[AgentResult]:
        """Execute a batch of independent tasks in parallel."""
        results = []

        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(tasks))) as pool:
            future_to_task = {
                pool.submit(self._run_with_retries, task, executor): task
                for task in tasks
            }

            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as exc:
                    Logger.error(f"[ParallelExecutor] Task {task.agent_name} raised: {exc}")
                    results.append(AgentResult(
                        agent_name=task.agent_name,
                        success=False,
                        error=str(exc),
                    ))

        return results

    def _run_with_retries(self, task: AgentTask, executor: Callable) -> AgentResult:
        """Run a task with retries and optional timeout."""
        retries = task.retries if task.retries > 0 else self.default_retries
        timeout = task.timeout or self.default_timeout
        last_error = None

        for attempt in range(1, retries + 2):
            start = time.perf_counter()
            try:
                if timeout and timeout > 0:
                    result = self._run_with_timeout(task, executor, timeout)
                else:
                    result = executor(task)

                result.attempts = attempt
                result.duration = time.perf_counter() - start

                if result.success:
                    return result

                last_error = result.error

            except Exception as exc:
                last_error = str(exc)
                result = AgentResult(
                    agent_name=task.agent_name,
                    success=False,
                    error=str(exc),
                    attempts=attempt,
                    duration=time.perf_counter() - start,
                )

            if attempt < retries + 1:
                Logger.warning(
                    f"[ParallelExecutor] Retrying {task.agent_name} "
                    f"({attempt}/{retries}): {last_error}"
                )

        return AgentResult(
            agent_name=task.agent_name,
            success=False,
            error=last_error,
            attempts=retries + 1,
        )

    def _run_with_timeout(self, task: AgentTask, executor: Callable, timeout: float) -> AgentResult:
        """Run a task with timeout using a separate thread."""
        result_container: List[AgentResult] = []

        def target():
            try:
                result_container.append(executor(task))
            except Exception as exc:
                result_container.append(AgentResult(
                    agent_name=task.agent_name,
                    success=False,
                    error=str(exc),
                ))

        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout)

        if thread.is_alive():
            return AgentResult(
                agent_name=task.agent_name,
                success=False,
                error=f"Timeout after {timeout}s",
            )

        return result_container[0] if result_container else AgentResult(
            agent_name=task.agent_name,
            success=False,
            error="No result returned",
        )

    def get_results(self) -> Dict[str, AgentResult]:
        """Get all execution results keyed by agent name."""
        return dict(self._results)

    def get_successful(self) -> List[AgentResult]:
        """Get all successful results."""
        return [r for r in self._results.values() if r.success]

    def get_failed(self) -> List[AgentResult]:
        """Get all failed results."""
        return [r for r in self._results.values() if not r.success]
