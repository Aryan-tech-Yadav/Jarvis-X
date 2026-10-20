"""Unified engineering graph backed by the existing KnowledgeGraph."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.intelligence.knowledge_graph import KnowledgeGraph

from .edge import EngineeringEdge
from .node import EngineeringNode


class EngineeringMemoryGraph:
    def __init__(self, graph: Optional[KnowledgeGraph] = None):
        self.graph = graph or KnowledgeGraph()

    def add_node(self, node_id: str, label: str, node_type: str,
                 properties: Optional[Dict[str, Any]] = None) -> EngineeringNode:
        self.graph.add_node(node_id, label, node_type, properties)
        return EngineeringNode(node_id, label, node_type, dict(properties or {}))

    def add_edge(self, source: str, target: str, relation: str,
                 properties: Optional[Dict[str, Any]] = None) -> EngineeringEdge:
        self.graph.add_edge(source, target, relation, properties=properties)
        return EngineeringEdge(source, target, relation, dict(properties or {}))

    def neighbors(self, node_id: str) -> List[EngineeringNode]:
        return [
            EngineeringNode(node.node_id, node.label, node.node_type, dict(node.properties))
            for node, _ in self.graph.get_neighbors(node_id)
        ]

    def find_similar(self, node_id: str) -> List[Dict[str, Any]]:
        return [{"node_id": candidate, "score": score}
                for candidate, score in self.graph.similarity(node_id)]

    def stats(self) -> Dict[str, Any]:
        return self.graph.stats()

