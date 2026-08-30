"""Multi-Agent Orchestrator - CEO of the engineering workflow.

Coordinates all specialized agents through a unified pipeline:
  Architect → Database → Backend → Frontend → QA → Repair → Documentation → Deployment → Reviewer

This is the entry point for autonomous software engineering.
"""

from __future__ import annotations

import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.agents.architect_agent import ArchitectAgent
from app.agents.backend_agent import BackendAgent
from app.agents.database_agent import DatabaseAgent
from app.agents.deployment_agent import DeploymentAgent
from app.agents.documentation_agent import DocumentationAgent
from app.agents.frontend_agent import FrontendAgent
from app.agents.message_bus import MessageBus
from app.agents.project_context import ProjectContext
from app.agents.repair_agent import RepairAgent
from app.agents.reviewer_agent import ReviewerAgent
from app.agents.testing_agent import TestingAgent
from app.core.logger import Logger
from app.orchestrator.scheduler import ExecutionSchedule, TaskScheduler
from app.orchestrator.task_graph import TaskGraph, TaskNode


@dataclass
class OrchestratorResult:
    """Result of the multi-agent orchestration."""

    workflow_id: str
    success: bool = False
    project_path: str = ""
    agents_executed: List[str] = field(default_factory=list)
    tasks_completed: int = 0
    tasks_failed: int = 0
    issues_repaired: int = 0
    review_score: Optional[float] = None
    review_issues: List[str] = field(default_factory=list)
    files_created: List[str] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)
    duration: float = 0.0
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "workflow_id": self.workflow_id,
            "success": self.success,
            "project_path": self.project_path,
            "agents_executed": list(self.agents_executed),
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "issues_repaired": self.issues_repaired,
            "review_score": self.review_score,
            "review_issues": list(self.review_issues),
            "files_created": list(self.files_created),
            "logs": list(self.logs),
            "duration": round(self.duration, 2),
            "error": self.error,
        }


class MultiAgentOrchestrator:
    """CEO orchestrator for multi-agent engineering workflow.

    Coordinates specialized agents to transform a user requirement
    into a complete, tested, documented, and deployed project.

    Pipeline:
    1. Architect - Design system architecture
    2. Database - Design database schema
    3. Backend - Generate backend code
    4. Frontend - Generate frontend code
    5. Testing - Write and run tests
    6. Repair - Fix failing tests and issues
    7. Documentation - Generate docs
    8. Deployment - Generate deployment configs
    9. Reviewer - Final code review
    """

    PIPELINE = [
        "architect",
        "database",
        "backend",
        "frontend",
        "testing",
        "repair",
        "documentation",
        "deployment",
        "reviewer",
    ]

    def __init__(self, state_dir: str = ".jarvis/orchestrator"):
        self.state_dir = state_dir
        os.makedirs(state_dir, exist_ok=True)

        # Core components
        self.message_bus = MessageBus()
        self.task_graph = TaskGraph()
        self.scheduler = TaskScheduler()

        # Agents (single responsibility principle)
        self.agents = {
            "architect": ArchitectAgent(),
            "database": DatabaseAgent(),
            "backend": BackendAgent(),
            "frontend": FrontendAgent(),
            "testing": TestingAgent(),
            "repair": RepairAgent(max_retries=3),
            "documentation": DocumentationAgent(),
            "deployment": DeploymentAgent(),
            "reviewer": ReviewerAgent(),
        }

    def run(self, requirement: str, base_path: Optional[str] = None) -> OrchestratorResult:
        """Run the complete multi-agent engineering pipeline.

        Args:
            requirement: Natural language project requirement.
            base_path: Optional base path for project generation.

        Returns:
            OrchestratorResult with complete execution results.
        """
        workflow_id = f"eng-{uuid.uuid4().hex[:12]}"
        started = time.perf_counter()
        Logger.info(f"[MultiAgentOrchestrator] Starting workflow {workflow_id}")
        Logger.info(f"[MultiAgentOrchestrator] Requirement: {requirement[:100]}")

        result = OrchestratorResult(workflow_id=workflow_id)

        try:
            # Phase 0: Initialize context and task graph
            context = self._initialize_context(requirement, base_path)
            self._build_task_graph(context)

            # Check for cycles
            cycles = self.task_graph.detect_cycles()
            if cycles:
                result.error = f"Circular dependencies detected: {cycles}"
                result.duration = time.perf_counter() - started
                return result

            # Phase 1: Execute pipeline
            for agent_name in self.PIPELINE:
                Logger.info(f"[MultiAgentOrchestrator] Executing agent: {agent_name}")
                agent = self.agents.get(agent_name)
                if not agent:
                    Logger.warning(f"[MultiAgentOrchestrator] Agent not found: {agent_name}")
                    continue

                # Send message to agent
                self.message_bus.send("orchestrator", agent_name, "execute", context)

                # Execute agent
                agent_start = time.perf_counter()
                try:
                    agent_result = agent.run(context)
                except Exception as exc:
                    Logger.error(f"[MultiAgentOrchestrator] Agent {agent_name} failed: {exc}")
                    agent_result = {"success": False, "error": str(exc), "output": str(exc)}

                agent_duration = time.perf_counter() - agent_start

                # Update context
                if isinstance(agent_result, dict):
                    context.update(**{k: v for k, v in agent_result.items() if k != "context"})
                    if "context" in agent_result and isinstance(agent_result["context"], ProjectContext):
                        context = agent_result["context"]

                # Track results
                result.agents_executed.append(agent_name)
                context.add_progress(agent_name, agent_result)

                success = agent_result.get("success", False) if isinstance(agent_result, dict) else False
                if success:
                    result.tasks_completed += 1
                    Logger.success(f"[MultiAgentOrchestrator] {agent_name} completed in {agent_duration:.2f}s")
                else:
                    result.tasks_failed += 1
                    error_msg = agent_result.get("error", agent_result.get("output", "Unknown")) if isinstance(agent_result, dict) else "Invalid result"
                    Logger.warning(f"[MultiAgentOrchestrator] {agent_name} failed: {error_msg}")

                # Handle repair cycle
                if agent_name == "testing" and not success:
                    Logger.info("[MultiAgentOrchestrator] Triggering repair cycle")
                    repair_agent = self.agents.get("repair")
                    if repair_agent:
                        repair_result = repair_agent.run(context)
                        result.issues_repaired += repair_result.get("output", {}).get("repaired", 0) if isinstance(repair_result, dict) else 0

                # Update task graph
                if agent_name in self.task_graph._nodes:
                    self.task_graph.mark_completed(agent_name)

            # Finalize
            result.success = result.tasks_failed == 0
            result.project_path = context.project_path
            result.files_created = [f.get("path", "") for f in context.files if isinstance(f, dict)]
            result.logs = list(context.logs)

            # Reviewer score
            review = self._get_context_value(context, "review")
            if isinstance(review, dict):
                result.review_score = 100.0 if review.get("approved") else 60.0
                result.review_issues = review.get("issues", [])

            # Repair count
            repair_output = self._get_context_value(context, "repair")
            if isinstance(repair_output, dict):
                output = repair_output.get("output", {})
                if isinstance(output, dict):
                    result.issues_repaired += output.get("repaired", 0)

            result.duration = time.perf_counter() - started
            Logger.success(f"[MultiAgentOrchestrator] Workflow {workflow_id} complete in {result.duration:.2f}s")
            return result

        except Exception as exc:
            result.error = str(exc)
            result.duration = time.perf_counter() - started
            Logger.error(f"[MultiAgentOrchestrator] Workflow failed: {exc}")
            return result

    def _initialize_context(self, requirement: str, base_path: Optional[str]) -> ProjectContext:
        """Initialize shared project context."""
        from app.engineering.requirement_analyzer import RequirementAnalyzer

        project_name = self._extract_project_name(requirement)
        context = ProjectContext(
            goal=requirement,
            project_name=project_name,
            project_path=base_path or os.path.join(os.getcwd(), "projects", project_name.lower().replace(" ", "_")),
        )
        context.add_log(f"Orchestrator initialized for: {requirement}")

        # Populate requirements from NLP analysis
        try:
            analyzer = RequirementAnalyzer()
            analysis = analyzer.analyze(requirement)
            context.requirements = analysis.to_dict()
            context.add_log(f"Requirements analyzed: {analysis.domain} / {analysis.project_type}")
        except Exception as exc:
            context.add_log(f"Requirement analysis failed: {exc}")

        return context

    def _build_task_graph(self, context: ProjectContext):
        """Build task graph from pipeline."""
        self.task_graph = TaskGraph()
        for i, agent_name in enumerate(self.PIPELINE):
            task = TaskNode(
                id=agent_name,
                title=f"{agent_name.title()} Task",
                description=f"Execute {agent_name} agent",
                agent=agent_name,
                dependencies=[self.PIPELINE[i - 1]] if i > 0 else [],
            )
            self.task_graph.add_task(task)

    @staticmethod
    def _extract_project_name(requirement: str) -> str:
        """Extract project name from requirement."""
        words = requirement.strip().split()
        # Look for "Build X" or "Create X" pattern
        for i, word in enumerate(words):
            if word.lower() in ("build", "create", "make", "develop") and i + 1 < len(words):
                return words[i + 1].strip('"\'')
        return words[0] if words else "project"

    @staticmethod
    def _get_context_value(context, key: str, default=None):
        """Get value from context safely."""
        if hasattr(context, key):
            return getattr(context, key)
        if isinstance(context, dict):
            return context.get(key, default)
        return default


class Orchestrator:
    """Legacy simple pipeline orchestrator for backward compatibility."""

    DEFAULT_WORKFLOW = ("planner", "executor", "reflection", "critic")

    def __init__(self, registry=None, workflow=None, max_steps=20, reasoning_engine=None, memory=None):
        from app.agents.agent_registry import AgentRegistry
        from app.memory.memory_manager import MemoryManager
        from app.orchestrator.task import Task

        self.registry = registry or AgentRegistry()
        self.workflow = tuple(workflow or self.DEFAULT_WORKFLOW)
        self.max_steps = max(1, max_steps)
        self.reasoning_engine = reasoning_engine
        self.memory = memory or MemoryManager()

    def execute(self, goal, task=None):
        from app.orchestrator.task import Task

        if task is None:
            if not isinstance(goal, str) or not goal.strip():
                raise ValueError("Goal cannot be empty")
            task = Task(goal=goal.strip())
        elif not isinstance(task, Task):
            raise TypeError("task must be a Task")

        current = task.current_step or self.workflow[0]
        for _ in range(self.max_steps):
            agent = self.registry.get(current)
            if agent is None:
                return self._failure(task, current, f"Unknown agent: {current}")

            initialize = getattr(agent, "initialize", None)
            if callable(initialize):
                initialize(task)
            try:
                result = agent.run(task)
            except Exception as error:
                result = {"success": False, "output": str(error), "error": str(error)}
            if not isinstance(result, dict):
                result = {"success": False, "output": "Agent returned an invalid result"}
            task.record(current, result)
            cleanup = getattr(agent, "cleanup", None)
            if callable(cleanup):
                cleanup(task)

            if current == "planner" and self.reasoning_engine is not None:
                reasoning_result = self.reasoning_engine.run(task.goal)
                task.memory_snapshot = self.memory.load_memory()
                task.record("reasoning", reasoning_result)
                if not reasoning_result.get("success", False):
                    return self._failure(task, "reasoning", reasoning_result.get("message", "Reasoning failed"))

            if not result.get("success", False):
                return self._failure(task, current, result.get("output", "Agent failed"))

            next_agent = result.get("next_agent") or self._next(current)
            if next_agent in (None, "complete", "done"):
                task.status = "completed"
                return {"success": True, "output": result.get("output"), "task": task}
            current = next_agent
            task.current_step = current

        return self._failure(task, current, "Maximum orchestration steps reached")

    def _next(self, current):
        try:
            index = self.workflow.index(current)
        except ValueError:
            return None
        return self.workflow[index + 1] if index + 1 < len(self.workflow) else None

    def _failure(self, task, agent, output):
        task.status = "failed"
        return {"success": False, "failed_agent": agent, "output": output, "task": task}
