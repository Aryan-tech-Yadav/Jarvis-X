"""Component relationships in engineering memory."""

from .graph import EngineeringMemoryGraph


class ComponentGraph:
    def __init__(self, graph=None):
        self.graph = graph or EngineeringMemoryGraph()

    def record(self, component_id: str, name: str, **properties):
        return self.graph.add_node(component_id, name, "component", properties)

    def link(self, source: str, target: str, relation: str = "uses"):
        return self.graph.add_edge(source, target, relation)

