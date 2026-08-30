"""Convenience operations for recording engineering relationships."""

from app.intelligence.knowledge_graph import KnowledgeGraph


class RelationshipManager:
    def __init__(self, graph=None):
        self.graph = graph or KnowledgeGraph()

    def link_project(self, project: str, technologies=(), modules=(), files=()):
        self.graph.add_node(project, project, "project")
        for label, node_type, relation in (
            [(item, "technology", "uses") for item in technologies]
            + [(item, "module", "contains") for item in modules]
            + [(item, "file", "includes") for item in files]
        ):
            node_id = f"{node_type}:{label}"
            self.graph.add_node(node_id, label, node_type)
            self.graph.add_edge(project, node_id, relation)
        return self.graph.stats()
