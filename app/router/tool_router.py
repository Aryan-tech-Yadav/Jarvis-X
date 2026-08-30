from app.core.logger import Logger
from app.project.project_manager import ProjectManager
from app.tools.project_tool import ProjectTool
from app.tools.tool_registry import ToolRegistry


class ToolRouter:

    def __init__(self, manager=None, registry=None):
        self.manager = manager or ProjectManager()
        self.registry = registry or ToolRegistry()
        if self.registry.get("project") is None:
            self.registry.register("project", ProjectTool(self.manager))

    def route(self, intent, request, current_project):
        if intent == "CREATE_PROJECT":
            result = self.registry.execute(
                "project",
                request,
                {"operation": "create", "current_project": current_project},
            )
            return {"action": intent, **result}

        if intent == "MODIFY_PROJECT":
            result = self.registry.execute(
                "project",
                request,
                {"operation": "modify", "current_project": current_project},
            )
            return self._result(intent, result)

        if intent == "ANALYZE_PROJECT":
            result = self.registry.execute(
                "project",
                request,
                {"operation": "analyze", "current_project": current_project},
            )
            return self._result(intent, result)

        if intent == "HELP":
            return {
                "action": intent,
                "result": "Commands: Create <project>, Modify <request>, Analyze, Exit",
                "current_project": current_project,
            }

        if intent == "GENERAL_CHAT":
            return {
                "action": intent,
                "result": "I am ready to help with your project.",
                "current_project": current_project,
            }

        if intent == "EXIT":
            return {"action": intent, "result": "Goodbye", "current_project": current_project}

        Logger.warning(f"Unsupported intent: {intent}")
        return {"action": "ERROR", "result": f"Unsupported intent: {intent}"}

    def _result(self, intent, result):
        if "error" in result:
            return {"action": "ERROR", "result": result["error"], "current_project": result.get("current_project")}
        return {"action": intent, **result}
