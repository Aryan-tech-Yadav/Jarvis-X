"""Execution Graph - DAG-based task orchestration.

Features:
  - Directed acyclic graph (DAG) of tasks
  - Parallel execution of independent nodes
  - Dependency resolution
  - Topological sorting
  - Cycle detection
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from collections import deque


class NodeStatus(str, Enum):
    """Node execution status."""
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ExecutionNode:
    """Node in execution graph."""
    node_id: str
    name: str
    handler: Callable
    dependencies: List[str] = field(default_factory=list)
    status: NodeStatus = NodeStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class ExecutionGraph:
    """Directed acyclic graph for task execution.

    Features:
      - Add nodes with dependencies
      - Topological sort
      - Parallel execution
      - Cycle detection
      - Status tracking
    """

    def __init__(self, name: str = "default"):
        self.name = name
        self._nodes: Dict[str, ExecutionNode] = {}
        self._edges: Dict[str, Set[str]] = {}
        self._reverse_edges: Dict[str, Set[str]] = {}
        self._completed: Set[str] = set()
        self._failed: Set[str] = set()
        self._lock = threading.RLock()

    def add_node(
        self,
        node_id: str,
        name: str,
        handler: Callable,
        dependencies: List[str] = None,
        metadata: Dict[str, Any] = None,
    ) -> ExecutionNode:
        """Add node to graph.

        Args:
            node_id: Unique node ID
            name: Human-readable name
            handler: Function to execute
            dependencies: List of node IDs this depends on
            metadata: Additional node metadata

        Returns:
            Created ExecutionNode
        """
        node = ExecutionNode(
            node_id=node_id,
            name=name,
            handler=handler,
            dependencies=dependencies or [],
            metadata=metadata or {},
        )
        self._nodes[node_id] = node
        self._edges.setdefault(node_id, set())
        self._reverse_edges.setdefault(node_id, set())

        for dep in node.dependencies:
            if dep not in self._nodes:
                raise ValueError(f"Unknown dependency: {dep}")
            self._edges.setdefault(dep, set()).add(node_id)
            self._reverse_edges.setdefault(node_id, set()).add(dep)

        return node

    def get_node(self, node_id: str) -> Optional[ExecutionNode]:
        """Get node by ID."""
        return self._nodes.get(node_id)

    def get_ready_nodes(self) -> List[ExecutionNode]:
        """Get nodes that are ready to execute.

        Returns nodes where all dependencies are completed.
        """
        ready = []
        for node_id, node in self._nodes.items():
            if node.status != NodeStatus.PENDING:
                continue
            deps = self._reverse_edges.get(node_id, set())
            if all(dep in self._completed for dep in deps):
                ready.append(node)
        return ready

    def mark_completed(self, node_id: str, result: Any = None):
        """Mark node as completed.

        Args:
            node_id: Node ID
            result: Node result
        """
        if node_id in self._nodes:
            node = self._nodes[node_id]
            node.status = NodeStatus.COMPLETED
            node.result = result
            node.finished_at = datetime.now().isoformat()
            if node.started_at:
                node.duration = (datetime.now() - datetime.fromisoformat(node.started_at)).total_seconds()
            self._completed.add(node_id)

    def mark_failed(self, node_id: str, error: str):
        """Mark node as failed.

        Args:
            node_id: Node ID
            error: Error message
        """
        if node_id in self._nodes:
            node = self._nodes[node_id]
            node.status = NodeStatus.FAILED
            node.error = error
            node.finished_at = datetime.now().isoformat()
            if node.started_at:
                node.duration = (datetime.now() - datetime.fromisoformat(node.started_at)).total_seconds()
            self._failed.add(node_id)

    def get_failed_nodes(self) -> List[ExecutionNode]:
        """Get all failed nodes."""
        return [node for node in self._nodes.values() if node.status == NodeStatus.FAILED]

    def topological_sort(self) -> List[str]:
        """Get nodes in topological order.

        Returns:
            List of node IDs in execution order
        """
        in_degree = {node_id: 0 for node_id in self._nodes}
        for node_id, deps in self._reverse_edges.items():
            in_degree[node_id] = len(deps)

        queue = deque([nid for nid, deg in in_degree.items() if deg == 0])
        sorted_nodes = []

        while queue:
            node_id = queue.popleft()
            sorted_nodes.append(node_id)
            for dependent in self._edges.get(node_id, set()):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        if len(sorted_nodes) != len(self._nodes):
            raise ValueError("Execution graph contains a cycle")
        return sorted_nodes

    def detect_cycle(self) -> Optional[List[str]]:
        """Detect cycles in graph.

        Returns:
            Cycle path if found, None otherwise
        """
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {node_id: WHITE for node_id in self._nodes}
        parent = {}

        def dfs(node_id: str) -> Optional[List[str]]:
            color[node_id] = GRAY
            for neighbor in self._edges.get(node_id, set()):
                if color.get(neighbor, WHITE) == GRAY:
                    cycle = [neighbor, node_id]
                    current = node_id
                    while current != neighbor:
                        current = parent.get(current)
                        if current is None:
                            break
                        cycle.append(current)
                    cycle.reverse()
                    return cycle
                elif color.get(neighbor, WHITE) == WHITE:
                    parent[neighbor] = node_id
                    result = dfs(neighbor)
                    if result:
                        return result
            color[node_id] = BLACK
            return None

        for node_id in self._nodes:
            if color.get(node_id, WHITE) == WHITE:
                cycle = dfs(node_id)
                if cycle:
                    return cycle
        return None

    def get_all_nodes(self) -> List[ExecutionNode]:
        """Get all nodes."""
        return list(self._nodes.values())

    def get_node_count(self) -> int:
        """Get total node count."""
        return len(self._nodes)

    def get_completed_count(self) -> int:
        """Get completed node count."""
        return len(self._completed)

    def get_failed_count(self) -> int:
        """Get failed node count."""
        return len(self._failed)

    def get_pending_count(self) -> int:
        """Get pending node count."""
        return sum(1 for node in self._nodes.values() if node.status == NodeStatus.PENDING)

    def is_completed(self) -> bool:
        """Check if all nodes completed."""
        return all(node.status in (NodeStatus.COMPLETED, NodeStatus.SKIPPED) for node in self._nodes.values())

    def is_failed(self) -> bool:
        """Check if any node failed."""
        return any(node.status == NodeStatus.FAILED for node in self._nodes.values())

    def to_dict(self) -> Dict[str, Any]:
        """Convert graph to dictionary."""
        return {
            "name": self.name,
            "nodes": [
                {
                    "node_id": node.node_id,
                    "name": node.name,
                    "status": node.status.value,
                    "dependencies": node.dependencies,
                    "error": node.error,
                    "duration": node.duration,
                }
                for node in self._nodes.values()
            ],
            "completed": len(self._completed),
            "failed": len(self._failed),
            "pending": self.get_pending_count(),
        }


# Thread lock helper
import threading

class threading_lock:
    """Simple threading lock wrapper."""
    def __enter__(self):
        self._lock = threading.RLock()
        self._lock.acquire()
        return self._lock

    def __exit__(self, *args):
        self._lock.release()
