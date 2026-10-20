"""Reusable solution relationships."""

from .graph import EngineeringMemoryGraph


class SolutionGraph:
    def __init__(self, graph=None):
        self.graph = graph or EngineeringMemoryGraph()

    def record(self, solution_id: str, title: str, **properties):
        return self.graph.add_node(solution_id, title, "solution", properties)

    def resolves(self, solution_id: str, bug_id: str):
        return self.graph.add_edge(solution_id, bug_id, "resolves")

