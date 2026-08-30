"""Frontend Agent - Generates frontend code for the project."""

from __future__ import annotations

from typing import Any, Dict

from app.agents.base_agent import BaseAgent
from app.agents.project_context import ProjectContext
from app.core.logger import Logger


class FrontendAgent(BaseAgent):
    """Generates frontend code and UI components."""

    agent_id = "frontend"
    capabilities = ("frontend", "ui", "react", "vue", "angular", "web")

    def run(self, context) -> Dict[str, Any]:
        if isinstance(context, dict):
            context = ProjectContext(**{k: v for k, v in context.items() if k in ProjectContext.__dataclass_fields__})
        
        requirements = context.requirements or {}
        frontend = requirements.get("frontend", "")
        
        if not frontend or not str(frontend).strip():
            context.add_log("No frontend required, skipping")
            return {
                "success": True,
                "output": {"skipped": True, "reason": "No frontend specified"},
                "context": context,
            }

        Logger.info(f"[FrontendAgent] Generating frontend: {frontend}")
        context.current_task = "frontend_generation"
        context.add_log(f"Starting frontend generation: {frontend}")

        # Frontend generation is delegated to the project builder in Phase 1
        # This agent marks the task as complete and logs the intent
        context.add_completed_task("frontend_generation")
        context.add_log(f"Frontend generation planned for: {frontend}")
        context.set_metric("frontend", frontend)
        
        return {
            "success": True,
            "output": {"frontend": frontend, "status": "planned"},
            "context": context,
        }
