"""Requirement Agent - Analyzes and structures project requirements."""

from __future__ import annotations

from typing import Any, Dict

from app.agents.base_agent import BaseAgent
from app.agents.project_context import ProjectContext
from app.engineering.requirement_analyzer import RequirementAnalyzer
from app.core.logger import Logger


class RequirementAgent(BaseAgent):
    """Analyzes raw user goals into structured engineering requirements."""

    agent_id = "requirement"
    capabilities = ("requirement", "analysis", "spec")

    def __init__(self, analyzer=None):
        self.analyzer = analyzer or RequirementAnalyzer()

    def run(self, context) -> Dict[str, Any]:
        if isinstance(context, dict):
            context = ProjectContext(**{k: v for k, v in context.items() if k in ProjectContext.__dataclass_fields__})
        
        goal = context.goal or ""
        if not goal:
            return {"success": False, "output": "No goal provided", "error": "No goal provided"}

        Logger.info(f"[RequirementAgent] Analyzing: {goal}")
        context.current_task = "requirement_analysis"
        context.add_log("Starting requirement analysis")

        result = self.analyzer.analyze(goal)
        if result.success:
            context.requirements = result.data or {}
            context.add_completed_task("requirement_analysis")
            context.add_log(f"Requirements analyzed: {result.metrics}")
            context.set_metric("requirement_time", result.duration)
            Logger.success(f"[RequirementAgent] Requirements: {result.metrics}")
        else:
            context.add_error(result.message or "Requirement analysis failed")
            context.add_log(f"Requirement analysis failed: {result.message}")

        return {
            "success": result.success,
            "output": result.data,
            "requirements": result.data,
            "context": context,
        }
