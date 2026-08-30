import json

from app.ai.ai_manager import AIManager
from app.planning.execution_plan import ExecutionPlan
from app.prompts.goal_planner_prompt import GOAL_PLANNER_PROMPT
from app.utils.json_utils import clean_json


class GoalPlanner:

    def __init__(self, ai=None):
        self.ai = ai or AIManager()

    def plan(self, goal):
        if not isinstance(goal, str) or not goal.strip():
            raise ValueError("Project goal cannot be empty")

        prompt = GOAL_PLANNER_PROMPT.format(goal=goal.strip())
        try:
            data = json.loads(clean_json(self.ai.ask(prompt)))
            return ExecutionPlan.from_dict(data)
        except (json.JSONDecodeError, TypeError, AttributeError, ValueError):
            return self._fallback_plan(goal)

    def _fallback_plan(self, goal):
        return ExecutionPlan(
            goal=goal.strip(),
            steps=[
                "Define the project structure and public interfaces",
                "Implement the core functionality",
                "Integrate components and handle errors",
                "Run validation and tests",
            ],
        )
