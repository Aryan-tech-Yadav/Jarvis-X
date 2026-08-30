"""Project-specific engineering graph operations."""

from .graph import EngineeringMemoryGraph


class ProjectGraph:
    def __init__(self, graph=None):
        self.graph = graph or EngineeringMemoryGraph()

    def record(self, project_id: str, name: str, domain: str = "general", **properties):
        return self.graph.add_node(project_id, name, "project",
                                   {"domain": domain, **properties})

    def link_component(self, project_id: str, component_id: str):
        return self.graph.add_edge(project_id, component_id, "contains")

