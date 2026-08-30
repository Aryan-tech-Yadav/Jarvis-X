"""Engineering project planning facade.

Wraps the existing goal planner so the engineering pipeline can consume
a stable execution plan contract.
"""

from app.core.logger import Logger
from app.core.results import ExecutionResult
from app.planning.execution_plan import ExecutionPlan
from app.planning.goal_planner import GoalPlanner


class ProjectPlanner:
    """Translate requirements into an executable project plan."""

    def __init__(self, planner=None):
        self.planner = planner or GoalPlanner()

    def plan(self, goal: str) -> ExecutionResult:
        if not isinstance(goal, str) or not goal.strip():
            return ExecutionResult.failed("Goal cannot be empty")

        try:
            plan = self.planner.plan(goal.strip())
            if isinstance(plan, ExecutionPlan):
                return ExecutionResult.completed(
                    data=plan.to_dict(),
                    message="Execution plan created",
                    metrics={"steps": len(plan.steps)},
                )

            steps = list(plan) if plan else []
            execution_plan = ExecutionPlan(goal=goal.strip(), steps=steps)
            return ExecutionResult.completed(
                data=execution_plan.to_dict(),
                message="Execution plan created",
                metrics={"steps": len(steps)},
            )
        except Exception as exc:
            Logger.error(f"Project planning failed: {exc}")
            return ExecutionResult.failed(str(exc))
