"""Clarifying-question generation."""

from app.analysis.requirements.clarifier import RequirementClarifier


class QuestionGenerator:
    def __init__(self, clarifier=None):
        self.clarifier = clarifier or RequirementClarifier()

    def generate(self, goal: str, requirements):
        return self.clarifier.clarify(goal, requirements, {}).questions

