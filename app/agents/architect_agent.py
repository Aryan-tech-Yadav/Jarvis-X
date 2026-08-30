"""Architect Agent - Designs project architecture and folder structure."""

from __future__ import annotations

from typing import Any, Dict

from app.agents.base_agent import BaseAgent
from app.agents.project_context import ProjectContext
from app.engineering.architecture_agent import ArchitectureAgent
from app.core.logger import Logger


class ArchitectAgent(BaseAgent):
    """Designs the project architecture and folder structure."""

    agent_id = "architect"
    capabilities = ("architecture", "architect", "design", "structure")

    def __init__(self, architecture_agent=None):
        self.architecture_agent = architecture_agent or ArchitectureAgent()

    def run(self, context) -> Dict[str, Any]:
        if isinstance(context, dict):
            context = ProjectContext(**{k: v for k, v in context.items() if k in ProjectContext.__dataclass_fields__})
        
        requirements = context.requirements or {}
        if not requirements:
            return {"success": False, "output": "No requirements available", "error": "No requirements"}

        Logger.info("[ArchitectAgent] Designing architecture")
        context.current_task = "architecture_design"
        context.add_log("Starting architecture design")

        result = self.architecture_agent.design(requirements)
        if result.success:
            context.architecture = result.data or {}
            context.add_completed_task("architecture_design")
            context.add_log(f"Architecture designed: {result.metrics}")
            context.set_metric("architecture_time", result.duration)
            Logger.success(f"[ArchitectAgent] Architecture: {result.metrics}")
        else:
            context.add_error(result.message or "Architecture design failed")
            context.add_log(f"Architecture design failed: {result.message}")

        return {
            "success": result.success,
            "output": result.data,
            "architecture": result.data,
            "context": context,
        }
