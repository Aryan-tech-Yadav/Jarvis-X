"""Data-driven clarification questions for ambiguous engineering goals."""

from __future__ import annotations

from app.analysis.requirements.clarifier import RequirementClarifier
from app.engineering.requirement_analyzer import RequirementAnalyzer


class ClarificationEngine:
    def __init__(self, analyzer=None, clarifier=None):
        self.analyzer = analyzer or RequirementAnalyzer()
        self.clarifier = clarifier or RequirementClarifier()

    def questions(self, goal: str):
        requirements = self.analyzer.analyze(goal)
        return list(self.clarifier.clarify(goal, requirements).questions)

    def analyze(self, goal: str):
        requirements = self.analyzer.analyze(goal)
        clarified = self.clarifier.clarify(goal, requirements)
        return {"questions": list(clarified.questions), "missing": list(clarified.missing)}
