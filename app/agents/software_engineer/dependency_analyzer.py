"""Dependency analysis facade."""

from app.engineering.dependency_resolver import DependencyResolver


class DependencyAnalyzer:
    def __init__(self, resolver=None):
        self.resolver = resolver or DependencyResolver()

    def analyze(self, tasks):
        return self.resolver.resolve(tasks)

