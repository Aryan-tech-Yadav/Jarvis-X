"""Task graph for engineering workflow execution.

Maintains a directed acyclic graph of tasks with dependencies,
enabling topological ordering, parallel execution, and critical path analysis.
"""

from __future__ import annotations

import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class TaskNode:
    """A single node in the task graph."""

    id: str
    title: str
    description: str
    agent: str = ""
    priority: str = "medium"
    status: str = "pending"
    estimated_hours: float = 1.0
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "agent": self.agent,
            "priority": self.priority,
            "status": self.status,
            "estimated_hours": self.estimated_hours,
            "dependencies": list(self.dependencies),
            "tags": list(self.tags),
            "metadata": dict(self.metadata),
        }


class TaskGraph:
    """Directed acyclic graph for task execution.

    Supports:
    - Adding tasks with dependencies
    - Cycle detection
    - Topological ordering
    - Parallel group identification
    - Critical path calculation
    """

    def __init__(self):
        self._nodes: Dict[str, TaskNode] = {}
        self._adjacency: Dict[str, List[str]] = defaultdict(list)
        self._reverse: Dict[str, List[str]] = defaultdict(list)

    def add_task(self, task: TaskNode) -> TaskNode:
        """Add a task to the graph.

        Args:
            task: TaskNode to add.

        Returns:
            The added TaskNode.

        Raises:
            ValueError: If task with same ID already exists.
        """
        if task.id in self._nodes:
            raise ValueError(f"Task already exists: {task.id}")
        self._nodes[task.id] = task
        for dep in task.dependencies:
            self._adjacency[dep].append(task.id)
            self._reverse[task.id].append(dep)
        return task

    def get_task(self, task_id: str) -> Optional[TaskNode]:
        """Get task by ID."""
        return self._nodes.get(task_id)

    def nodes(self) -> List[TaskNode]:
        """Return graph nodes in insertion order."""
        return list(self._nodes.values())

    def get_ready_tasks(self) -> List[TaskNode]:
        """Get tasks that are ready to execute (all dependencies completed)."""
        ready = []
        for task in self._nodes.values():
            if task.status != "pending":
                continue
            deps_ready = all(
                self._nodes[dep].status == "completed"
                for dep in task.dependencies
                if dep in self._nodes
            )
            if deps_ready:
                ready.append(task)
        return sorted(ready, key=lambda t: {"high": 0, "medium": 1, "low": 2}.get(t.priority, 1))

    def mark_completed(self, task_id: str):
        """Mark a task as completed."""
        if task_id in self._nodes:
            self._nodes[task_id].status = "completed"

    def mark_failed(self, task_id: str):
        """Mark a task as failed."""
        if task_id in self._nodes:
            self._nodes[task_id].status = "failed"

    def detect_cycles(self) -> List[List[str]]:
        """Detect circular dependencies.

        Returns:
            List of cycles, where each cycle is a list of task IDs.
        """
        cycles = []
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {tid: WHITE for tid in self._nodes}

        def dfs(node: str, path: List[str]):
            color[node] = GRAY
            path.append(node)
            for neighbor in self._adjacency.get(node, []):
                if neighbor not in color:
                    continue
                if color[neighbor] == GRAY:
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    if cycle not in cycles:
                        cycles.append(cycle)
                elif color[neighbor] == WHITE:
                    dfs(neighbor, path)
            path.pop()
            color[node] = BLACK

        for tid in self._nodes:
            if color.get(tid, WHITE) == WHITE:
                dfs(tid, [])

        return cycles

    def topological_sort(self) -> List[str]:
        """Return tasks in topological order.

        Returns:
            List of task IDs in execution order.
        """
        in_degree = {tid: 0 for tid in self._nodes}
        for tid, deps in self._reverse.items():
            in_degree[tid] = len(deps)

        queue = deque([tid for tid, deg in in_degree.items() if deg == 0])
        ordered = []

        while queue:
            node = queue.popleft()
            ordered.append(node)
            for neighbor in self._adjacency.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return ordered

    def get_parallel_groups(self) -> List[List[str]]:
        """Identify groups of tasks that can run in parallel.

        Returns:
            List of task ID groups.
        """
        groups = []
        completed: Set[str] = set()
        remaining = set(self.topological_sort())

        while remaining:
            ready = []
            for tid in remaining:
                task = self._nodes[tid]
                deps = set(task.dependencies)
                if deps.issubset(completed):
                    ready.append(tid)

            if not ready:
                break

            groups.append(ready)
            completed.update(ready)
            remaining -= set(ready)

        return groups

    def get_critical_path(self) -> Tuple[List[str], float]:
        """Calculate critical path (longest path through graph).

        Returns:
            Tuple of (task IDs in critical path, total duration).
        """
        earliest_finish: Dict[str, float] = {}
        earliest_start: Dict[str, float] = {}

        def calc(task_id: str) -> float:
            if task_id in earliest_finish:
                return earliest_finish[task_id]

            task = self._nodes[task_id]
            duration = task.estimated_hours
            deps = task.dependencies

            if not deps:
                earliest_start[task_id] = 0.0
            else:
                earliest_start[task_id] = max(calc(dep) for dep in deps if dep in self._nodes)

            earliest_finish[task_id] = earliest_start[task_id] + duration
            return earliest_finish[task_id]

        for tid in self._nodes:
            calc(tid)

        if not earliest_finish:
            return [], 0.0

        total_duration = max(earliest_finish.values())
        critical_path = []

        # Trace back from end tasks
        end_tasks = [tid for tid, ef in earliest_finish.items() if ef == total_duration]
        if end_tasks:
            current = end_tasks[0]
            while current:
                critical_path.append(current)
                task = self._nodes[current]
                deps = task.dependencies
                if not deps:
                    break
                current = max(
                    (d for d in deps if d in self._nodes),
                    key=lambda d: earliest_finish.get(d, 0),
                    default=None,
                )

        critical_path.reverse()
        return critical_path, total_duration

    def get_stats(self) -> Dict[str, Any]:
        """Get graph statistics."""
        return {
            "total_tasks": len(self._nodes),
            "pending": sum(1 for t in self._nodes.values() if t.status == "pending"),
            "completed": sum(1 for t in self._nodes.values() if t.status == "completed"),
            "failed": sum(1 for t in self._nodes.values() if t.status == "failed"),
            "total_dependencies": sum(len(t.dependencies) for t in self._nodes.values()),
            "cycles": len(self.detect_cycles()),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serialize graph to dictionary."""
        return {
            "tasks": [t.to_dict() for t in self._nodes.values()],
            "adjacency": {k: list(v) for k, v in self._adjacency.items()},
            "stats": self.get_stats(),
        }
