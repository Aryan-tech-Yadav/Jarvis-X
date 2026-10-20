"""Constraint detection facade."""

from app.requirements.constraint_analyzer import ConstraintAnalyzer


class ConstraintDetector:
    def __init__(self, analyzer=None):
        self.analyzer = analyzer or ConstraintAnalyzer()

    def detect(self, goal: str) -> list[str]:
        return self.analyzer.analyze(goal)

