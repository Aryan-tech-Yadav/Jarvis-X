"""Engineering task graph (DAG) with dependency resolution.

Converts an engineering plan into an executable directed acyclic graph
where each node represents a project task and edges represent dependencies.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class TaskStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TaskNode:
    """Single node in the engineering task graph."""

    def __init__(self, name: str, payload: Optional[Dict[str, Any]] = None):
        self.name = name
        self.payload = payload or {}
        self.status = TaskStatus.PENDING
        self.dependencies: List[str] = []
        self.dependents: List[str] = []
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.attempts: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "dependencies": list(self.dependencies),
            "dependents": list(self.dependents),
            "attempts": self.attempts,
            "error": self.error,
            "payload": dict(self.payload),
        }


class TaskGraph:
    """Directed acyclic graph of engineering tasks.

    Supports:
    - Node and edge creation
    - Topological execution ordering
    - Ready-node detection
    - Status updates
    - Retry / strategy switching
    """

    def __init__(self):
        self._nodes: Dict[str, TaskNode] = {}
        self._edges: Dict[str, Set[str]] = {}

    def add_node(self, name: str, payload: Optional[Dict[str, Any]] = None) -> TaskNode:
        if name in self._nodes:
            return self._nodes[name]
        node = TaskNode(name=name, payload=payload)
        self._nodes[name] = node
        self._edges[name] = set()
        return node

    def add_edge(self, from_node: str, to_node: str):
        if from_node not in self._nodes:
            self.add_node(from_node)
        if to_node not in self._nodes:
            self.add_node(to_node)

        self._edges[from_node].add(to_node)
        self._nodes[to_node].dependencies.append(from_node)
        self._nodes[from_node].dependents.append(to_node)

    def ready_nodes(self) -> List[TaskNode]:
        ready = []
        for node in self._nodes.values():
            if node.status == TaskStatus.PENDING:
                deps_done = all(
                    self._nodes[d].status == TaskStatus.COMPLETED for d in node.dependencies
                )
                if deps_done:
                    node.status = TaskStatus.READY
                    ready.append(node)
        return ready

    def mark_completed(self, name: str, result: Optional[Dict[str, Any]] = None):
        node = self._nodes.get(name)
        if node:
            node.status = TaskStatus.COMPLETED
            node.result = result

    def mark_failed(self, name: str, error: str):
        node = self._nodes.get(name)
        if node:
            node.status = TaskStatus.FAILED
            node.error = error
            node.attempts += 1

    def mark_running(self, name: str):
        node = self._nodes.get(name)
        if node:
            node.status = TaskStatus.RUNNING
            node.attempts += 1

    def reset_for_retry(self, name: str):
        node = self._nodes.get(name)
        if node and node.status == TaskStatus.FAILED:
            node.status = TaskStatus.PENDING
            node.error = None

    def topological_order(self) -> List[str]:
        in_degree = {name: 0 for name in self._nodes}
        for name, edges in self._edges.items():
            for target in edges:
                in_degree[target] += 1

        queue = [name for name, deg in in_degree.items() if deg == 0]
        order = []

        while queue:
            current = queue.pop(0)
            order.append(current)
            for target in self._edges.get(current, []):
                in_degree[target] -= 1
                if in_degree[target] == 0:
                    queue.append(target)

        if len(order) != len(self._nodes):
            raise ValueError("Task graph contains a cycle")

        return order

    def all_completed(self) -> bool:
        return all(node.status == TaskStatus.COMPLETED for node in self._nodes.values())

    def any_failed(self) -> bool:
        return any(node.status == TaskStatus.FAILED for node in self._nodes.values())

    def node(self, name: str) -> Optional[TaskNode]:
        return self._nodes.get(name)

    def nodes(self) -> Dict[str, TaskNode]:
        return dict(self._nodes)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": [node.to_dict() for node in self._nodes.values()],
            "order": self.topological_order(),
        }

    @classmethod
    def from_plan(cls, plan: Dict[str, Any]) -> TaskGraph:
        """Build a task graph from a planning payload (list of steps or plan dict)."""
        graph = cls()
        steps = []
        if isinstance(plan, dict):
            steps = plan.get("steps", plan.get("tasks", []))
        elif isinstance(plan, list):
            steps = plan

        if not steps:
            graph.add_node("generate_project", payload={"action": "generate_project"})
            return graph

        previous = None
        for step in steps:
            if isinstance(step, str):
                name = step.strip()
                payload = {"action": name}
            elif isinstance(step, dict):
                name = str(step.get("name", step.get("step", ""))).strip()
                payload = step
            else:
                continue

            if not name:
                continue

            node = graph.add_node(name, payload=payload)
            if previous is not None:
                graph.add_edge(previous, name)
            previous = name

        return graph
