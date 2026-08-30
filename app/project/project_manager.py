import os

from app.core.logger import Logger
from app.project.project_builder import ProjectBuilder
from app.project.project_analyzer import ProjectAnalyzer
from app.project.project_modifier import ProjectModifier
from app.planning.goal_planner import GoalPlanner
from app.planning.plan_executor import PlanExecutor
from app.reflection.reflection_agent import ReflectionAgent
from app.tools.tool_manager import ToolManager


class ProjectManager:

    def __init__(self, builder=None):
        self.builder = builder or ProjectBuilder()
        self.analyzer = ProjectAnalyzer()
        self.modifier = ProjectModifier(self.analyzer)
        self.goal_planner = GoalPlanner()
        self.plan_executor = PlanExecutor(self, reflection=ReflectionAgent())
        self.tools = ToolManager()

    def _project_exists(self, base_path):
        return isinstance(base_path, str) and bool(base_path.strip()) and os.path.isdir(base_path)

    def create_project(self, prompt):
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("Project prompt cannot be empty")

        Logger.info("Creating project...")
        project_path = self.builder.build(prompt.strip())
        Logger.success(f"Project created: {project_path}")
        return project_path

    def create(self, prompt):
        return self.create_project(prompt)

    def analyze_project(self, base_path):
        Logger.info(f"Analyzing project: {base_path}")
        return self.analyzer.analyze(base_path)

    def modify_project(self, base_path, request):
        if not isinstance(request, str) or not request.strip():
            raise ValueError("Modification request cannot be empty")

        if not self._project_exists(base_path):
            error = "Project path not found"
            Logger.error(f"Modifying project: {base_path} -> {error}")
            return False, error

        Logger.info(f"Modifying project: {base_path}")
        success, result = self.modifier.modify(base_path, request.strip())
        if success:
            Logger.success(f"Modified files: {', '.join(result)}")
        else:
            Logger.error(result)
        return success, result

    def plan_project(self, goal):
        Logger.info(f"Planning project goal: {goal}")
        plan = self.goal_planner.plan(goal)
        Logger.success(f"Execution plan created with {len(plan.steps)} steps")
        return plan

    def execute_plan(self, plan, base_path):
        return self.plan_executor.execute(base_path, plan)

    def resume_execution(self, plan, base_path):
        return self.plan_executor.resume_execution(base_path, plan)

    def execute_collaboration(self, goal, project_path=None, context=None, **options):
        """Run the Phase 1 specialized-agent project workflow.

        The import is intentionally local: the regular project manager remains
        usable without constructing every collaboration service.
        """
        from app.orchestrator.agent_orchestrator import AgentOrchestrator

        return AgentOrchestrator(project_manager=self, **options).run(goal, project_path, context)

    def execute_collaboration_result(self, goal, project_path=None, context=None, **options):
        """Run collaboration with the shared `ExecutionResult` response contract."""
        from app.orchestrator.agent_orchestrator import AgentOrchestrator

        return AgentOrchestrator(project_manager=self, **options).run_result(goal, project_path, context)

    def validate_project(self, base_path):
        if not self._project_exists(base_path):
            return False, "Project path not found"

        summary = self.analyzer.analyze(base_path)
        project = {
            "folders": self._project_folders(base_path),
            "files": [
                {"name": file_name, "type": "python" if file_name.endswith(".py") else "txt"}
                for file_name in summary["files"]
                if file_name not in {"README.md", "requirements.txt"}
            ],
        }
        return self.builder.validator.validate(project, base_path)

    def repair_project(self, base_path, validation_message):
        if not self._project_exists(base_path):
            Logger.error(f"Repairing project: {base_path} -> Project path not found")
            return []

        summary = self.analyzer.analyze(base_path)
        project = {
            "files": [
                {"name": file_name, "type": "python" if file_name.endswith(".py") else "txt"}
                for file_name in summary["files"]
            ],
        }
        return self.builder.repair.repair(project, base_path, validation_message)

    def _project_folders(self, base_path):
        folders = []
        for root, directories, _ in os.walk(base_path):
            directories[:] = [directory for directory in directories if directory not in {".git", ".venv", "venv", "__pycache__"}]
            for directory in directories:
                folders.append(os.path.relpath(os.path.join(root, directory), base_path))
        return folders
