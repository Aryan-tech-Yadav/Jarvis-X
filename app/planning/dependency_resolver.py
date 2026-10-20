from app.reasoning.dependency_graph import DependencyGraph


class DependencyResolver:
    def order(self, tasks, dependencies=None):
        graph = DependencyGraph()
        dependencies = dependencies or {}
        for task in tasks:
            graph.add(task, dependencies.get(task, []))
        return graph.order()