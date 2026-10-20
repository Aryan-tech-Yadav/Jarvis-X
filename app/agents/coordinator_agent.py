from app.agents.agent_context import AgentContext
from app.agents.task_dispatcher import TaskDispatcher


class CoordinatorAgent:
    def __init__(self, planner, dispatcher, max_replans=1):
        self.planner = planner
        self.dispatcher = dispatcher
        self.max_replans = max(0, max_replans)

    def create_plan(self, goal):
        return self.planner.plan(goal)

    def assign_task(self, task):
        return self.dispatcher.dispatch(task)

    def execute_plan(self, goal, context=None):
        plan = self.create_plan(goal)
        context = context or AgentContext(goal=goal, plan=plan)
        tasks = plan.get("tasks", plan) if isinstance(plan, dict) else plan
        results = [self.assign_task(task) for task in (tasks or [])]
        return {"success": all(item.get("success", False) for item in results), "plan": plan, "results": results, "context": context}

    def replan(self, goal):
        return self.create_plan(goal)

    def finish(self, results):
        return {"success": True, "results": results}