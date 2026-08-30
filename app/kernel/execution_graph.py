"""Deterministic dependency graph used by the autonomous execution kernel.

The graph keeps scheduling policy deliberately small: it knows which nodes are
eligible to run, but it never executes their payloads.  A dependency points
from a node to work that must finish before that node can run.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Iterable, Mapping


@dataclass(frozen=True, slots=True)
class ExecutionNode:
    """One unit of work in an :class:`ExecutionGraph`."""

    id: str
    payload: Any = None
    priority: int = 0


class ExecutionGraph:
    """A typed, deterministic directed acyclic graph of execution nodes.

    Higher numeric priorities are returned first when multiple nodes are ready.
    Node identifiers break every tie, so a graph produces the same schedule
    independent of insertion order.
    """

    def __init__(self) -> None:
        self._nodes: dict[str, ExecutionNode] = {}
        self._dependencies: dict[str, set[str]] = {}

    @property
    def nodes(self) -> Mapping[str, ExecutionNode]:
        """Return a shallow, immutable-to-the-graph view of known nodes."""

        return dict(self._nodes)

    def add_node(self, id: str, payload: Any = None, priority: int = 0) -> ExecutionNode:
        """Add and return a node.

        Identifiers must be non-empty strings and may only be registered once.
        Dependencies are deliberately added separately so misspelled references
        are rejected immediately by :meth:`add_dependency`.
        """

        if not isinstance(id, str) or not id:
            raise ValueError("Node id must be a non-empty string")
        if not isinstance(priority, int):
            raise TypeError("Node priority must be an integer")
        if id in self._nodes:
            raise ValueError(f"Duplicate execution node: {id}")

        node = ExecutionNode(id=id, payload=payload, priority=priority)
        self._nodes[id] = node
        self._dependencies[id] = set()
        return node

    def add_dependency(self, node: str, dependency: str) -> None:
        """Require *dependency* to finish before *node* can run.

        Both endpoints must already exist.  An attempted cyclic edge is rolled
        back before a :class:`ValueError` is raised, leaving the graph usable.
        """

        self._require_node(node)
        self._require_node(dependency)
        if dependency in self._dependencies[node]:
            return

        self._dependencies[node].add(dependency)
        if self._contains_cycle():
            self._dependencies[node].remove(dependency)
            raise ValueError(
                f"Dependency {dependency!r} -> {node!r} would create a cycle"
            )

    def get_node(self, node_id: str) -> dict[str, Any]:
        """Return a defensive mapping for one node's scheduler-facing data."""

        self._require_node(node_id)
        return self._node_mapping(self._nodes[node_id])

    def ready(self, completed: Iterable[str] | None = None) -> list[dict[str, Any]]:
        """Return unfinished nodes whose dependencies are all complete.

        ``completed`` represents externally persisted execution state.  Unknown
        ids are rejected instead of silently treating a typo as completed work.
        Returned mappings expose ``id``, ``payload``, and ``priority`` for the
        scheduler, without allowing it to mutate graph-owned data.
        """

        done = self._completed_set(completed)
        ready_ids = self._ordered(
            node_id
            for node_id, dependencies in self._dependencies.items()
            if node_id not in done and dependencies.issubset(done)
        )
        return [self.get_node(node_id) for node_id in ready_ids]

    def levels(self) -> list[list[str]]:
        """Return deterministic topological execution levels.

        Nodes in a single nested list can run in parallel once the preceding
        levels have completed.  A cycle raises ``ValueError`` defensively; it
        cannot normally exist because ``add_dependency`` rejects one.
        """

        remaining = set(self._nodes)
        completed: set[str] = set()
        result: list[list[str]] = []

        while remaining:
            level = self._ordered(
                node_id
                for node_id in remaining
                if self._dependencies[node_id].issubset(completed)
            )
            if not level:
                raise ValueError("Execution graph contains a cycle")
            result.append(level)
            completed.update(level)
            remaining.difference_update(level)

        return result

    def dependents(self, id: str) -> list[str]:
        """Return the direct downstream dependents of ``id`` in schedule order."""

        self._require_node(id)
        return self._ordered(
            node_id
            for node_id, dependencies in self._dependencies.items()
            if id in dependencies
        )

    def critical_path(self) -> list[str]:
        """Return the longest dependency chain, with stable lexical tie-breaking."""

        paths: dict[str, tuple[str, ...]] = {}
        for level in self.levels():
            for node_id in level:
                parent_paths = [paths[parent] for parent in self._dependencies[node_id]]
                if parent_paths:
                    paths[node_id] = self._longest(parent_paths) + (node_id,)
                else:
                    paths[node_id] = (node_id,)

        return list(self._longest(paths.values())) if paths else []

    def to_dict(self) -> dict[str, Any]:
        """Return a portable graph record suitable for an execution checkpoint."""

        return {
            "nodes": [self._node_mapping(self._nodes[node_id]) for node_id in self._ordered(self._nodes)],
            "dependencies": {node_id: sorted(dependencies) for node_id, dependencies in self._dependencies.items()},
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ExecutionGraph":
        """Restore a graph after validating every persisted node and edge."""

        if not isinstance(value, Mapping):
            raise TypeError("Execution graph payload must be a mapping")
        graph = cls()
        for node in value.get("nodes", ()):
            graph.add_node(node["id"], deepcopy(node.get("payload")), node.get("priority", 0))
        for node_id, dependencies in dict(value.get("dependencies", {})).items():
            for dependency in dependencies:
                graph.add_dependency(node_id, dependency)
        return graph

    def _completed_set(self, completed: Iterable[str] | None) -> set[str]:
        done = set(completed or ())
        unknown = done.difference(self._nodes)
        if unknown:
            names = ", ".join(sorted(unknown))
            raise ValueError(f"Unknown completed execution nodes: {names}")
        return done

    def _contains_cycle(self) -> bool:
        try:
            self.levels()
        except ValueError:
            return True
        return False

    def _ordered(self, node_ids: Iterable[str]) -> list[str]:
        return sorted(
            node_ids,
            key=lambda node_id: (-self._nodes[node_id].priority, node_id),
        )

    def _require_node(self, node_id: str) -> None:
        if node_id not in self._nodes:
            raise ValueError(f"Unknown execution node: {node_id}")

    @staticmethod
    def _node_mapping(node: ExecutionNode) -> dict[str, Any]:
        return {
            "id": node.id,
            "payload": deepcopy(node.payload),
            "priority": node.priority,
        }

    @staticmethod
    def _longest(paths: Iterable[tuple[str, ...]]) -> tuple[str, ...]:
        """Choose longest then lexically earliest path for deterministic ties."""

        return min(paths, key=lambda path: (-len(path), path))
