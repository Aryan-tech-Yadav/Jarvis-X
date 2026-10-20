"""Turn goal analysis into an executable dependency graph."""

from __future__ import annotations

from typing import Iterable, Optional

from app.orchestrator.task_graph import TaskGraph, TaskNode
from app.planning.goal_analyzer import GoalAnalysis, GoalAnalyzer


class TaskDecomposer:
    """Create independent work nodes while preserving engineering dependencies."""

    def __init__(self, goal_analyzer: Optional[GoalAnalyzer] = None):
        self.goal_analyzer = goal_analyzer or GoalAnalyzer()

    def decompose(self, goal: str | GoalAnalysis) -> TaskGraph:
        analysis = goal if isinstance(goal, GoalAnalysis) else self.goal_analyzer.analyze(goal)
        graph = TaskGraph()
        deliverables = set(analysis.deliverables)

        self._add(graph, "research", "Research", "researcher")
        self._add(graph, "architecture", "Architecture", "planner", ["research"])
        if "Database" in deliverables:
            self._add(graph, "database", "Database", "database", ["architecture"])
        if "Backend" in deliverables:
            dependencies = ["architecture"]
            if "Database" in deliverables:
                dependencies.append("database")
            self._add(graph, "backend", "Backend", "coder", dependencies)
        if "Frontend" in deliverables:
            dependencies = ["architecture"]
            if "Backend" in deliverables:
                dependencies.append("backend")
            self._add(graph, "frontend", "Frontend", "coder", dependencies)

        implementation = [
            task_id
            for task_id in ("backend", "frontend", "database")
            if graph.get_task(task_id) is not None
        ]
        self._add(graph, "testing", "Testing", "tester", implementation or ["architecture"])
        self._add(graph, "repair", "Repair", "repair", ["testing"])
        self._add(graph, "documentation", "Documentation", "documentation", ["repair"])
        return graph

    @staticmethod
    def _add(graph: TaskGraph, task_id: str, title: str, agent: str, dependencies: Optional[Iterable[str]] = None) -> None:
        graph.add_task(
            TaskNode(
                id=task_id,
                title=title,
                description=f"Complete the {title.lower()} stage",
                agent=agent,
                dependencies=list(dependencies or []),
            )
        )
