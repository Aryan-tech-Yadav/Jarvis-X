from app.agents.base_agent import BaseAgent


class PlannerAgent(BaseAgent):
    """Creates a high-level implementation plan without changing files."""

    agent_id = "planner"
    capabilities = ("plan", "planning", "project")

    def __init__(self, planner=None):
        self.planner = planner

    def run(self, context):
        goal = self.context_value(context, "goal", "")
        if not isinstance(goal, str) or not goal.strip():
            return {"success": False, "output": "A non-empty goal is required to plan work."}

        try:
            plan = self._create_plan(goal.strip())
        except Exception as error:
            return {"success": False, "output": str(error), "error": str(error)}

        self.update_context(context, "plan", plan)
        return {"success": True, "output": plan, "plan": plan}

    def _create_plan(self, goal):
        if self.planner is None:
            return [
                "Clarify requirements and project architecture",
                "Create the application structure",
                "Implement the requested functionality",
                "Validate and test the project",
                "Document the completed feature",
            ]
        plan_method = getattr(self.planner, "plan", self.planner)
        plan = plan_method(goal)
        if not plan:
            raise ValueError("Planner did not return a plan")
        return plan
