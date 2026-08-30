"""Knowledge Graph for Jarvis-X.

Builds a graph of engineering concepts, projects, and relationships.
Instead of simple memory, creates connections:
  Hospital → Appointment → Doctor → Patient → Billing
  Clinic → Doctor → Appointment (automatically connected)
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class GraphNode:
    """Node in the knowledge graph."""

    node_id: str
    label: str
    node_type: str = "concept"  # project, module, pattern, technology, domain
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "label": self.label,
            "node_type": self.node_type,
            "properties": dict(self.properties),
            "created_at": self.created_at,
        }


@dataclass
class GraphEdge:
    """Edge in the knowledge graph."""

    source: str
    target: str
    relation: str = "related_to"
    weight: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "target": self.target,
            "relation": self.relation,
            "weight": self.weight,
            "properties": dict(self.properties),
            "created_at": self.created_at,
        }


class KnowledgeGraph:
    """In-memory knowledge graph for engineering concepts."""

    def __init__(self, graph_path: str = "data/knowledge_graph.json"):
        self.graph_path = graph_path
        self._nodes: Dict[str, GraphNode] = {}
        self._edges: List[GraphEdge] = []
        os.makedirs(os.path.dirname(graph_path) or ".", exist_ok=True)
        self._load()

    def _load(self):
        if not os.path.exists(self.graph_path):
            return
        try:
            with open(self.graph_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                for node_id, node_data in data.get("nodes", {}).items():
                    self._nodes[node_id] = GraphNode(**node_data)
                for edge_data in data.get("edges", []):
                    self._edges.append(GraphEdge(**edge_data))
        except (OSError, json.JSONDecodeError, TypeError):
            pass

    def _save(self):
        try:
            with open(self.graph_path, "w", encoding="utf-8") as f:
                json.dump({
                    "nodes": {k: v.to_dict() for k, v in self._nodes.items()},
                    "edges": [e.to_dict() for e in self._edges],
                }, f, indent=2, default=str)
        except OSError:
            pass

    def add_node(self, node_id: str, label: str, node_type: str = "concept",
                 properties: Optional[Dict[str, Any]] = None) -> GraphNode:
        """Add a node to the graph."""
        node = GraphNode(
            node_id=node_id,
            label=label,
            node_type=node_type,
            properties=properties or {},
        )
        self._nodes[node_id] = node
        self._save()
        return node

    def add_edge(self, source: str, target: str, relation: str = "related_to",
                 weight: float = 1.0, properties: Optional[Dict[str, Any]] = None) -> GraphEdge:
        """Add an edge between two nodes."""
        edge = GraphEdge(
            source=source,
            target=target,
            relation=relation,
            weight=weight,
            properties=properties or {},
        )
        self._edges.append(edge)
        self._save()
        return edge

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        return self._nodes.get(node_id)

    def get_neighbors(self, node_id: str) -> List[Tuple[GraphNode, str]]:
        """Get neighboring nodes with their relation type."""
        neighbors = []
        for edge in self._edges:
            if edge.source == node_id:
                neighbor = self._nodes.get(edge.target)
                if neighbor:
                    neighbors.append((neighbor, edge.relation))
            elif edge.target == node_id:
                neighbor = self._nodes.get(edge.source)
                if neighbor:
                    neighbors.append((neighbor, edge.relation))
        return neighbors

    def find_shortest_path(self, source: str, target: str) -> List[str]:
        """BFS shortest path between two nodes."""
        if source not in self._nodes or target not in self._nodes:
            return []
        if source == target:
            return [source]
        visited = {source}
        queue = [(source, [source])]
        while queue:
            current, path = queue.pop(0)
            for neighbor, _ in self.get_neighbors(current):
                if neighbor.node_id == target:
                    return path + [neighbor.node_id]
                if neighbor.node_id not in visited:
                    visited.add(neighbor.node_id)
                    queue.append((neighbor.node_id, path + [neighbor.node_id]))
        return []

    def similarity(self, node_id: str) -> List[Tuple[str, float]]:
        """Find most similar nodes by shared neighbors."""
        if node_id not in self._nodes:
            return []
        source_neighbors = {n.node_id for n, _ in self.get_neighbors(node_id)}
        scores = []
        for other_id, other_node in self._nodes.items():
            if other_id == node_id:
                continue
            other_neighbors = {n.node_id for n, _ in self.get_neighbors(other_id)}
            overlap = len(source_neighbors & other_neighbors)
            if overlap > 0:
                scores.append((other_id, overlap / max(1, len(source_neighbors | other_neighbors))))
        scores.sort(key=lambda pair: pair[1], reverse=True)
        return scores[:10]

    def stats(self) -> Dict[str, Any]:
        node_types: Dict[str, int] = {}
        for node in self._nodes.values():
            node_types[node.node_type] = node_types.get(node.node_type, 0) + 1
        return {
            "total_nodes": len(self._nodes),
            "total_edges": len(self._edges),
            "node_types": node_types,
        }

    def all_nodes(self) -> List[GraphNode]:
        return list(self._nodes.values())

    def all_edges(self) -> List[GraphEdge]:
        return list(self._edges)
