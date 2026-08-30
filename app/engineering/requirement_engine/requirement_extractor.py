"""Requirement extraction facade."""

from app.agents.software_engineer.requirement_analyzer import RequirementAnalyzer


class RequirementExtractor:
    def __init__(self, analyzer=None):
        self.analyzer = analyzer or RequirementAnalyzer()

    def extract(self, goal: str):
        return self.analyzer.analyze(goal)

