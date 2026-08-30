"""Parsing boundary for natural-language project goals."""

from app.agents.software_engineer.requirement_analyzer import RequirementAnalyzer


class RequirementParser:
    def __init__(self, analyzer=None):
        self.analyzer = analyzer or RequirementAnalyzer()

    def parse(self, goal: str):
        return self.analyzer.analyze(goal)
