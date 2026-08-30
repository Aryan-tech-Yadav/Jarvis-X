from app.agents.base_agent import BaseAgent
from app.project.project_manager import ProjectManager


class CoderAgent(BaseAgent):
    """Delegates project creation, modification, and repair to ProjectManager."""

    agent_id = "coder"
    capabilities = ("code", "coding", "create", "modify", "repair")

    def __init__(self, project_manager=None):
        self.project_manager = project_manager or ProjectManager()

    def run(self, context):
        operation = self.context_value(context, "operation", "create")
        goal = self.context_value(context, "goal", "")
        project_path = self.context_value(context, "project_path") or self.context_value(context, "base_path")
        request = self.context_value(context, "repair_request") or self.context_value(context, "request") or goal

        try:
            if operation == "modify":
                success, output = self.project_manager.modify_project(project_path, request)
            elif operation == "repair":
                output = self.project_manager.repair_project(project_path, request)
                success = output is not None
            else:
                output = self.project_manager.create_project(goal)
                success = bool(output)
                if success:
                    self.update_context(context, "project_path", output)
        except Exception as error:
            return {"success": False, "output": str(error), "error": str(error)}

        return {"success": bool(success), "output": output, "operation": operation}
