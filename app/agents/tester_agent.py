import os

from app.agents.base_agent import BaseAgent
from app.project.project_manager import ProjectManager
from app.project.project_runner import ProjectRunner
from app.project.project_tester import ProjectTester


class TesterAgent(BaseAgent):
    """Uses the existing project validator to report a normalized test result."""

    __test__ = False  # Prevent pytest from collecting this agent as a test suite
    agent_id = "tester"
    capabilities = ("test", "testing", "validation", "validate")

    def __init__(self, project_manager=None, tester=None, runner=None):
        self.project_manager = project_manager or ProjectManager()
        self.tester = tester or ProjectTester()
        self.runner = runner or ProjectRunner()

    def run(self, context):
        project_path = self.context_value(context, "project_path") or self.context_value(context, "base_path")
        if not project_path:
            return {"success": False, "output": {"passed": False, "errors": ["Project path is required."]}}

        try:
            passed, message = self.project_manager.validate_project(project_path)
        except Exception as error:
            passed, message = False, str(error)

        errors = [] if passed else [line for line in str(message).splitlines() if line] or [str(message)]
        if passed:
            errors.extend(self._syntax_errors(project_path))
        if passed and self.context_value(context, "run_project", False):
            ran, runtime_output = self.runner.run(project_path)
            if not ran:
                errors.append(str(runtime_output))
        passed = not errors
        output = {"passed": bool(passed), "errors": errors}
        self.update_context(context, "validation", output)
        return {"success": bool(passed), "output": output}

    def _syntax_errors(self, project_path):
        errors = []
        if not os.path.isdir(project_path):
            return errors
        for root, _, files in os.walk(project_path):
            for filename in files:
                if not filename.endswith(".py"):
                    continue
                path = os.path.join(root, filename)
                try:
                    with open(path, "r", encoding="utf-8") as source:
                        passed, message = self.tester.test({"name": filename, "type": "python"}, source.read())
                except OSError as error:
                    passed, message = False, str(error)
                if not passed:
                    errors.append(str(message))
        return errors
