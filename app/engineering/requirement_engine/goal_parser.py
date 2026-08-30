"""Normalize user goals before requirement extraction."""


class GoalParser:
    def parse(self, goal: str) -> str:
        if not isinstance(goal, str) or not goal.strip():
            raise ValueError("Project goal cannot be empty")
        return " ".join(goal.strip().split())

