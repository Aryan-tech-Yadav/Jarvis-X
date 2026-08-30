"""Clarification question generation."""

from app.analysis.requirements.clarifier import RequirementClarifier


class ClarificationEngine:
    def __init__(self, clarifier=None):
        self.clarifier = clarifier or RequirementClarifier()

    def questions(self, goal: str, requirements) -> list[str]:
        self.clarifier.clarify(goal, requirements)
        return list(requirements.questions)

