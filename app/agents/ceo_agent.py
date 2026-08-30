"""CEO Agent - Orchestrates the entire multi-agent engineering pipeline."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.agents.base_agent import BaseAgent
from app.agents.project_context import ProjectContext
from app.core.logger import Logger


class CeoAgent(BaseAgent):
    """Top-level orchestrator that delegates to specialized agents."""

    agent_id = "ceo"
    capabilities = ("ceo", "orchestrate", "manager", "lead")

    def __init__(self, registry=None):
        self.registry = registry

    def run(self, context) -> Dict[str, Any]:
        if isinstance(context, dict):
            context = ProjectContext(**{k: v for k, v in context.items() if k in ProjectContext.__dataclass_fields__})
        
        goal = context.goal or ""
        if not goal:
            return {"success": False, "output": "No goal provided", "error": "No goal provided"}

        Logger.info(f"[CeoAgent] Orchestrating project: {goal}")
        context.status = "orchestrating"
        context.current_task = "ceo_orchestration"
        context.add_log(f"CEO started orchestration for: {goal}")

        # Determine which agents are needed based on requirements
        required_agents = self._determine_agents(context)
        context.metadata["required_agents"] = required_agents
        context.add_log(f"Required agents: {', '.join(required_agents)}")

        return {
            "success": True,
            "output": {
                "goal": goal,
                "required_agents": required_agents,
                "next_agent": required_agents[0] if required_agents else None,
            },
            "context": context,
        }

    def _determine_agents(self, context: ProjectContext) -> List[str]:
        """Determine which agents are needed for this project."""
        agents = ["requirement", "architect"]
        
        req = context.requirements or {}
        # Always include backend for code generation
        agents.append("backend")
        
        frontend = req.get("frontend", "")
        if frontend and str(frontend).strip():
            agents.append("frontend")
        
        database = req.get("database", "")
        if database and str(database).strip():
            agents.append("database")
        
        if req.get("testing", True):
            agents.extend(["tester", "reviewer"])
        
        agents.append("documentation")
        
        return agents

    def review(self, context) -> Dict[str, Any]:
        return {"success": True, "output": {"approved": True, "notes": "CEO review complete"}}

    def report(self, context) -> Dict[str, Any]:
        if isinstance(context, ProjectContext):
            return {"success": True, "output": context.to_dict()}
        return {"success": True, "output": context}
