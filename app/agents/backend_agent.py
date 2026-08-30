"""Backend Agent - Generates backend code for the project."""

from __future__ import annotations

from typing import Any, Dict

from app.agents.base_agent import BaseAgent
from app.agents.project_context import ProjectContext
from app.project.project_builder import ProjectBuilder
from app.core.logger import Logger


class BackendAgent(BaseAgent):
    """Generates backend code and project structure."""

    agent_id = "backend"
    capabilities = ("backend", "api", "server", "code", "generate")

    def __init__(self, builder=None):
        self.builder = builder or ProjectBuilder()

    def run(self, context) -> Dict[str, Any]:
        if isinstance(context, dict):
            context = ProjectContext(**{k: v for k, v in context.items() if k in ProjectContext.__dataclass_fields__})
        
        goal = context.goal or ""
        if not goal:
            return {"success": False, "output": "No goal provided", "error": "No goal provided"}

        Logger.info("[BackendAgent] Generating project")
        context.current_task = "backend_generation"
        context.add_log("Starting backend generation")

        try:
            project_path = self.builder.build(goal)
            context.project_path = project_path
            context.add_completed_task("backend_generation")
            context.add_log(f"Project generated at: {project_path}")
            context.set_metric("project_path", project_path)
            Logger.success(f"[BackendAgent] Project generated: {project_path}")
            return {
                "success": True,
                "output": {"project_path": project_path},
                "project_path": project_path,
                "context": context,
            }
        except Exception as exc:
            error_msg = f"Backend generation failed: {exc}"
            context.add_error(error_msg)
            context.add_log(error_msg)
            Logger.error(f"[BackendAgent] {error_msg}")
            return {"success": False, "output": error_msg, "error": error_msg, "context": context}
