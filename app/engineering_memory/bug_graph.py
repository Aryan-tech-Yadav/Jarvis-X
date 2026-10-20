"""Bug and affected-component relationships."""

from .graph import EngineeringMemoryGraph


class BugGraph:
    def __init__(self, graph=None):
        self.graph = graph or EngineeringMemoryGraph()

    def record(self, bug_id: str, title: str, **properties):
        return self.graph.add_node(bug_id, title, "bug", properties)

    def affects(self, bug_id: str, component_id: str):
        return self.graph.add_edge(bug_id, component_id, "affects")

