class DependencyGraph:
    def __init__(self):
        self.edges = {}

    def add(self, node, dependencies=None):
        self.edges.setdefault(node, set()).update(dependencies or [])
        for dependency in dependencies or []:
            self.edges.setdefault(dependency, set())

    def order(self):
        graph = {node: set(deps) for node, deps in self.edges.items()}
        result = []
        while graph:
            ready = sorted(node for node, deps in graph.items() if not deps)
            if not ready:
                raise ValueError("Circular dependency detected")
            result.extend(ready)
            for node in ready:
                graph.pop(node)
            for deps in graph.values():
                deps.difference_update(ready)
        return result