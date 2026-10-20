"""Dependency relationships in engineering memory."""

from .graph import EngineeringMemoryGraph


class DependencyGraph:
    def __init__(self, graph=None):
        self.graph = graph or EngineeringMemoryGraph()

    def add(self, component_id: str, dependency_id: str):
        return self.graph.add_edge(component_id, dependency_id, "depends_on")

