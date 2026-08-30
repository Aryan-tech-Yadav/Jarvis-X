"""Agent Orchestrator - Coordinates multiple specialized agents.

Flow:
  CEO Agent
    -> Requirement Agent
    -> Architect Agent
    -> Backend Agent
    -> Frontend Agent (if needed)
    -> Database Agent (if needed)
    -> Testing Agent
    -> Security Agent
    -> Deployment Agent
    -> Reviewer Agent
    -> Documentation Agent
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from app.agents.agent_registry import AgentRegistry
from app.agents.project_context import ProjectContext
from app.agents.ceo_agent import CeoAgent
from app.agents.requirement_agent import RequirementAgent
from app.agents.architect_agent import ArchitectAgent
from app.agents.backend_agent import BackendAgent
from app.agents.frontend_agent import FrontendAgent
from app.agents.database_agent import DatabaseAgent
from app.agents.tester_agent import TesterAgent
from app.agents.security_agent import SecurityAgent
from app.agents.deployment_agent import DeploymentAgent
from app.agents.reviewer_agent import ReviewerAgent
from app.agents.documentation_agent import DocumentationAgent
from app.core.logger import Logger
from app.events.event_bus import EventBus
from app.events.event_types import (
    PROJECT_STARTED,
    REQUIREMENTS_DONE,
    ARCHITECTURE_DONE,
    BACKEND_DONE,
    FRONTEND_DONE,
    DATABASE_DONE,
    TESTING_DONE,
    SECURITY_DONE,
    DEPLOYMENT_DONE,
    PROJECT_FINISHED,
    PROJECT_COMPLETED,
)
from app.core.results import ExecutionResult


class AgentOrchestrator:
    """Coordinate the multi-agent engineering pipeline."""

    PIPELINE = ("ceo", "requirement", "architect", "backend", "frontend", "database", "testing", "security", "deployment", "reviewer", "documentation")

    def __init__(self, registry=None, event_bus=None):
        self.registry = registry or self._default_registry()
        self.event_bus = event_bus or EventBus()
        self._subscribe_events()

    def _default_registry(self) -> AgentRegistry:
        registry = AgentRegistry()
        registry.register(CeoAgent())
        registry.register(RequirementAgent())
        registry.register(ArchitectAgent())
        registry.register(BackendAgent())
        registry.register(FrontendAgent())
        registry.register(DatabaseAgent())
        registry.register(TesterAgent())
        registry.register(SecurityAgent())
        registry.register(DeploymentAgent())
        registry.register(ReviewerAgent())
        registry.register(DocumentationAgent())
        return registry

    def _subscribe_events(self):
        self.event_bus.subscribe(PROJECT_STARTED, self._on_project_started)
        self.event_bus.subscribe(PROJECT_FINISHED, self._on_project_finished)
        self.event_bus.subscribe(PROJECT_COMPLETED, self._on_project_completed)

    def _on_project_started(self, event):
        Logger.info(f"[Orchestrator] Project started: {event.payload}")

    def _on_project_finished(self, event):
        Logger.info(f"[Orchestrator] Project finished: {event.payload}")

    def _on_project_completed(self, event):
        Logger.info(f"[Orchestrator] Project completed: {event.payload}")

    def run(self, goal: str, context: Optional[Dict[str, Any]] = None) -> ExecutionResult:
        """Run the full multi-agent pipeline for a goal."""
        started = time.perf_counter()
        
        # Initialize context
        if context is None:
            context = {}
        if isinstance(context, dict):
            project_context = ProjectContext(goal=goal)
            for key, value in context.items():
                if key in ProjectContext.__dataclass_fields__:
                    setattr(project_context, key, value)
        else:
            project_context = context

        Logger.info(f"[Orchestrator] Starting pipeline for: {goal}")
        self.event_bus.publish(PROJECT_STARTED, {"goal": goal})

        # Determine required agents from CEO
        ceo = self.registry.get("ceo")
        if not ceo:
            return ExecutionResult.failed("CEO agent not registered", duration=time.perf_counter() - started)

        ceo_result = ceo.run(project_context)
        if not ceo_result.get("success"):
            return ExecutionResult.failed(
                ceo_result.get("output", "CEO failed"),
                data=project_context.to_dict(),
                duration=time.perf_counter() - started,
            )

        required_agents = ceo_result.get("output", {}).get("required_agents", [])
        project_context = ceo_result.get("context", project_context)

        # Execute agents in pipeline order
        for agent_name in required_agents:
            agent = self.registry.get(agent_name)
            if not agent:
                Logger.warning(f"[Orchestrator] Agent not found: {agent_name}")
                continue

            Logger.info(f"[Orchestrator] Running agent: {agent_name}")
            project_context.current_task = agent_name
            
            try:
                result = agent.run(project_context)
                project_context = result.get("context", project_context)
                
                if not result.get("success"):
                    error = result.get("error", result.get("output", f"{agent_name} failed"))
                    project_context.add_error(str(error))
                    Logger.error(f"[Orchestrator] {agent_name} failed: {error}")
                    # Continue with other agents unless it's a critical failure
                    continue

                # Emit success event
                self._emit_success_event(agent_name, result)
                
            except Exception as exc:
                error_msg = f"{agent_name} error: {exc}"
                project_context.add_error(error_msg)
                Logger.error(f"[Orchestrator] {error_msg}")

        # Finalize
        project_context.status = "completed"
        project_context.current_task = ""
        duration = time.perf_counter() - started
        
        self.event_bus.publish(PROJECT_FINISHED, project_context.to_dict())
        self.event_bus.publish(PROJECT_COMPLETED, project_context.to_dict())

        message = f"Pipeline completed for: {goal}"
        if project_context.errors:
            message += f" with {len(project_context.errors)} errors"

        return ExecutionResult(
            success=len(project_context.errors) == 0,
            status="completed" if not project_context.errors else "completed_with_errors",
            message=message,
            data=project_context.to_dict(),
            metrics=project_context.metrics,
            warnings=[],
            errors=project_context.errors,
            artifacts=[project_context.project_path] if project_context.project_path else [],
            duration=duration,
        )

    def _emit_success_event(self, agent_name: str, result: Dict[str, Any]):
        event_map = {
            "requirement": REQUIREMENTS_DONE,
            "architect": ARCHITECTURE_DONE,
            "backend": BACKEND_DONE,
            "frontend": FRONTEND_DONE,
            "database": DATABASE_DONE,
            "tester": TESTING_DONE,
            "security": SECURITY_DONE,
            "deployment": DEPLOYMENT_DONE,
        }
        event_type = event_map.get(agent_name)
        if event_type:
            self.event_bus.publish(event_type, result.get("output"))

    execute = run
