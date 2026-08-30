"""Engineering execution engine.

Executes a task graph with configurable retries, backoff, and strategy
switching when a task fails repeatedly.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from app.core.logger import Logger
from app.core.results import ExecutionResult
from app.engineering.task_graph import TaskGraph, TaskNode, TaskStatus


class RetryStrategy(str, Enum):
    FIXED = "fixed"
    EXPONENTIAL = "exponential"
    ADAPTIVE = "adaptive"


@dataclass
class ExecutionPolicy:
    """Configurable execution policy for the execution engine."""

    max_retries: int = 3
    retry_strategy: RetryStrategy = RetryStrategy.FIXED
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 10.0
    fail_fast: bool = False
    continue_on_failure: bool = False


@dataclass
class ExecutionResultArtifact:
    """Captures the outcome of a single task execution."""

    node_name: str
    success: bool
    output: Any = None
    error: Optional[str] = None
    duration: float = 0.0
    attempts: int = 0


Handler = Callable[[TaskNode], ExecutionResultArtifact]


class ExecutionEngine:
    """Execute a TaskGraph with retry, backoff, and strategy switching."""

    def __init__(self, policy: Optional[ExecutionPolicy] = None):
        self.policy = policy or ExecutionPolicy()
        self.artifacts: List[ExecutionResultArtifact] = []
        self.strategy_switches: List[Dict[str, Any]] = []

    def execute(
        self,
        graph: TaskGraph,
        handler: Handler,
        strategy_handler: Optional[Callable[[TaskNode, str], Optional[Handler]]] = None,
    ) -> ExecutionResult:
        """Execute all nodes in the graph using the provided handler.

        Args:
            graph: The task graph to execute.
            handler: A callable that accepts a TaskNode and returns an ExecutionResultArtifact.
            strategy_handler: Optional callable that receives a failed node and the
                current strategy hint, and may return a new handler for retry.

        Returns:
            ExecutionResult summarizing the full execution.
        """
        self.artifacts = []
        self.strategy_switches = []
        started = time.perf_counter()

        while not graph.all_completed():
            ready = graph.ready_nodes()
            if not ready:
                if graph.any_failed():
                    break
                # No ready nodes and no failures means deadlock or empty graph
                break

            node = ready[0]
            graph.mark_running(node.name)
            Logger.info(f"[ExecutionEngine] Running: {node.name}")

            artifact = self._execute_with_retry(node, handler, strategy_handler)
            self.artifacts.append(artifact)

            if artifact.success:
                graph.mark_completed(node.name, artifact.output)
                Logger.success(f"[ExecutionEngine] Completed: {node.name}")
            else:
                graph.mark_failed(node.name, artifact.error or "Unknown error")
                Logger.error(f"[ExecutionEngine] Failed: {node.name} -> {artifact.error}")

                if self.policy.fail_fast:
                    break

        duration = time.perf_counter() - started
        success = graph.all_completed() and not graph.any_failed()

        return ExecutionResult(
            success=success,
            status="completed" if success else "failed",
            message="Execution engine finished",
            data={
                "graph": graph.to_dict(),
                "artifacts": [a.__dict__ for a in self.artifacts],
                "strategy_switches": list(self.strategy_switches),
            },
            metrics={
                "total_tasks": len(graph.nodes()),
                "completed": sum(1 for n in graph.nodes().values() if n.status == TaskStatus.COMPLETED),
                "failed": sum(1 for n in graph.nodes().values() if n.status == TaskStatus.FAILED),
                "duration": round(duration, 3),
            },
            errors=[a.error for a in self.artifacts if not a.success],
            duration=duration,
        )

    def _execute_with_retry(
        self,
        node: TaskNode,
        handler: Handler,
        strategy_handler: Optional[Callable[[TaskNode, str], Optional[Handler]]],
    ) -> ExecutionResultArtifact:
        attempt = 0
        last_error = "Unknown error"
        current_handler = handler
        strategy = self.policy.retry_strategy.value

        while attempt < self.policy.max_retries:
            attempt += 1
            node_start = time.perf_counter()
            try:
                artifact = current_handler(node)
                artifact.attempts = attempt
                artifact.duration = time.perf_counter() - node_start
                if artifact.success:
                    return artifact
                last_error = artifact.error or "Unknown error"
            except Exception as exc:
                last_error = str(exc)
                artifact = ExecutionResultArtifact(
                    node_name=node.name,
                    success=False,
                    error=last_error,
                    attempts=attempt,
                    duration=time.perf_counter() - node_start,
                )

            if attempt < self.policy.max_retries:
                delay = self._compute_delay(attempt)
                Logger.warning(
                    f"[ExecutionEngine] Retrying {node.name} in {delay:.2f}s "
                    f"(attempt {attempt + 1}/{self.policy.max_retries})"
                )
                time.sleep(delay)

                # Strategy switching on retry
                if strategy_handler is not None:
                    new_handler = strategy_handler(node, strategy)
                    if new_handler is not None and new_handler != current_handler:
                        self.strategy_switches.append({
                            "node": node.name,
                            "attempt": attempt,
                            "old_strategy": strategy,
                            "new_strategy": strategy,
                        })
                        current_handler = new_handler

        return ExecutionResultArtifact(
            node_name=node.name,
            success=False,
            error=last_error,
            attempts=attempt,
            duration=0.0,
        )

    def _compute_delay(self, attempt: int) -> float:
        strategy = self.policy.retry_strategy
        if strategy == RetryStrategy.EXPONENTIAL:
            delay = self.policy.base_delay_seconds * (2 ** (attempt - 1))
        elif strategy == RetryStrategy.ADAPTIVE:
            delay = self.policy.base_delay_seconds * (1.5 ** (attempt - 1))
        else:
            delay = self.policy.base_delay_seconds
        return min(delay, self.policy.max_delay_seconds)
