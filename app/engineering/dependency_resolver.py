"""Dependency resolver for engineering workflow.

Resolves task dependencies using topological sorting and identifies
parallel execution opportunities.
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple


@dataclass
class ResolvedDependencies:
    """Resolved dependency order for tasks."""

    ordered_tasks: List[str] = field(default_factory=list)
    parallel_groups: List[List[str]] = field(default_factory=list)
    critical_path: List[str] = field(default_factory=list)
    total_duration: float = 0.0
    has_cycles: bool = False

    def to_dict(self) -> dict:
        return {
            "ordered_tasks": list(self.ordered_tasks),
            "parallel_groups": [list(g) for g in self.parallel_groups],
            "critical_path": list(self.critical_path),
            "total_duration": round(self.total_duration, 1),
            "has_cycles": self.has_cycles,
        }


class DependencyResolver:
    """Resolve task dependencies using topological sorting.

    Supports:
    - Cycle detection
    - Parallel task identification
    - Critical path analysis
    """

    def resolve(self, tasks: List[dict]) -> ResolvedDependencies:
        """Resolve dependencies for a list of tasks.

        Args:
            tasks: List of task dictionaries with 'id', 'dependencies', 'estimated_hours'.

        Returns:
            ResolvedDependencies with ordered tasks and parallel groups.
        """
        if not tasks:
            return ResolvedDependencies()

        # Build dependency graph
        task_map = {t["id"]: t for t in tasks}
        graph: Dict[str, List[str]] = defaultdict(list)
        in_degree: Dict[str, int] = defaultdict(int)

        for task in tasks:
            task_id = task["id"]
            if task_id not in in_degree:
                in_degree[task_id] = 0
            for dep in task.get("dependencies", []):
                graph[dep].append(task_id)
                in_degree[task_id] += 1

        # Detect cycles using DFS
        has_cycles = self._detect_cycles(graph, set(task_map.keys()))

        # Topological sort (Kahn's algorithm)
        ordered = []
        queue = deque([tid for tid in task_map if in_degree.get(tid, 0) == 0])

        while queue:
            # Process all nodes with in_degree 0 (parallel group)
            current_level = list(queue)
            queue.clear()
            ordered.extend(current_level)

            for node in current_level:
                for neighbor in graph.get(node, []):
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)

        if len(ordered) != len(task_map):
            # Has cycles, return partial result
            return ResolvedDependencies(
                ordered_tasks=ordered,
                has_cycles=True,
            )

        # Identify parallel groups
        parallel_groups = self._identify_parallel_groups(ordered, graph, task_map)

        # Calculate critical path
        critical_path, total_duration = self._calculate_critical_path(task_map, graph)

        return ResolvedDependencies(
            ordered_tasks=ordered,
            parallel_groups=parallel_groups,
            critical_path=critical_path,
            total_duration=total_duration,
            has_cycles=False,
        )

    def _detect_cycles(self, graph: Dict[str, List[str]], nodes: Set[str]) -> bool:
        """Detect cycles using DFS."""
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {node: WHITE for node in nodes}

        def dfs(node: str) -> bool:
            color[node] = GRAY
            for neighbor in graph.get(node, []):
                if neighbor not in color:
                    continue
                if color[neighbor] == GRAY:
                    return True
                if color[neighbor] == WHITE and dfs(neighbor):
                    return True
            color[node] = BLACK
            return False

        for node in nodes:
            if color.get(node, WHITE) == WHITE:
                if dfs(node):
                    return True
        return False

    def _identify_parallel_groups(self, ordered: List[str], graph: Dict[str, List[str]], task_map: dict) -> List[List[str]]:
        """Identify tasks that can run in parallel."""
        groups = []
        completed = set()
        remaining = set(ordered)

        while remaining:
            # Find tasks with all dependencies completed
            ready = []
            for task_id in remaining:
                task = task_map[task_id]
                deps = set(task.get("dependencies", []))
                if deps.issubset(completed):
                    ready.append(task_id)

            if not ready:
                break

            groups.append(ready)
            completed.update(ready)
            remaining -= set(ready)

        return groups

    def _calculate_critical_path(self, task_map: dict, graph: Dict[str, List[str]]) -> Tuple[List[str], float]:
        """Calculate critical path (longest path through dependency graph)."""
        # Calculate earliest finish times
        earliest_finish: Dict[str, float] = {}
        earliest_start: Dict[str, float] = {}

        def calc_earliest(task_id: str) -> float:
            if task_id in earliest_finish:
                return earliest_finish[task_id]

            task = task_map[task_id]
            duration = task.get("estimated_hours", 1.0)
            deps = task.get("dependencies", [])

            if not deps:
                earliest_start[task_id] = 0.0
            else:
                earliest_start[task_id] = max(calc_earliest(dep) for dep in deps)

            earliest_finish[task_id] = earliest_start[task_id] + duration
            return earliest_finish[task_id]

        for task_id in task_map:
            calc_earliest(task_id)

        # Find critical path (tasks with earliest_start == earliest_finish - duration)
        total_duration = max(earliest_finish.values()) if earliest_finish else 0.0
        critical_path = []

        # Trace back from end
        end_tasks = [tid for tid, ef in earliest_finish.items() if ef == total_duration]
        if end_tasks:
            current = end_tasks[0]
            while current:
                critical_path.append(current)
                task = task_map[current]
                deps = task.get("dependencies", [])
                if not deps:
                    break
                # Find dependency with latest finish
                current = max(deps, key=lambda d: earliest_finish.get(d, 0))

        critical_path.reverse()
        return critical_path, total_duration
