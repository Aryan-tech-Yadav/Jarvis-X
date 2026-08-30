"""Scalable multi-agent orchestrator.

Extends the existing AgentOrchestrator with:
  - Parallel agent execution
  - Dependency-aware scheduling
  - Inter-agent communication via MessageBus
  - Self-improving repair loops
  - Execution history and performance tracking
"""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional

from app.agents.agent_registry import AgentRegistry
from app.agents.execution_history import ExecutionHistory, ExecutionRecord
from app.agents.message_bus import MessageBus
from app.agents.parallel_executor import ParallelAgentExecutor, AgentTask, AgentResult
from app.agents.self_improving_repair import SelfImprovingRepairLoop
from app.agents.project_context import ProjectContext
from app.core.logger import Logger
from app.core.results import ExecutionResult
from app.events.event_bus import EventBus
from app.events.event_types import PROJECT_STARTED, PROJECT_FINISHED, PROJECT_COMPLETED


class ScalableOrchestrator:
    """Orchestrate multi-agent execution at scale.

    Supports:
      - Sequential execution for dependent tasks
      - Parallel execution for independent tasks
      - Message-based inter-agent communication
      - Automatic repair on failure
      - Performance tracking and optimization
    """

    PIPELINE_AGENTS = ("ceo", "requirement", "architect", "backend", "frontend", "database", "testing", "security", "deployment", "reviewer", "documentation")

    def __init__(
        self,
        registry: Optional[AgentRegistry] = None,
        event_bus: Optional[EventBus] = None,
        message_bus: Optional[MessageBus] = None,
        execution_history: Optional[ExecutionHistory] = None,
        max_parallel: int = 4,
        enable_repair: bool = True,
    ):
        self.registry = registry or AgentRegistry()
        self.event_bus = event_bus or EventBus()
        self.message_bus = message_bus or MessageBus()
        self.execution_history = execution_history or ExecutionHistory()
        self.parallel_executor = ParallelAgentExecutor(max_workers=max_parallel)
        self.repair_loop = SelfImprovingRepairLoop(execution_history=self.execution_history, message_bus=self.message_bus) if enable_repair else None
        self.max_parallel = max_parallel
        self._subscribe_events()

    def _subscribe_events(self):
        self.event_bus.subscribe(PROJECT_STARTED, self._on_project_started)
        self.event_bus.subscribe(PROJECT_FINISHED, self._on_project_finished)
        self.event_bus.subscribe(PROJECT_COMPLETED, self._on_project_completed)

    def _on_project_started(self, event):
        Logger.info(f"[ScalableOrchestrator] Project started: {event.payload}")

    def _on_project_finished(self, event):
        Logger.info(f"[ScalableOrchestrator] Project finished: {event.payload}")

    def _on_project_completed(self, event):
        Logger.info(f"[ScalableOrchestrator] Project completed: {event.payload}")

    def run(self, goal: str, context: Optional[Dict[str, Any]] = None) -> ExecutionResult:
        """Run the full multi-agent pipeline for a goal.

        Args:
            goal: Project goal.
            context: Optional initial context.

        Returns:
            ExecutionResult with pipeline outcome.
        """
        started = time.perf_counter()

        if context is None:
            context = {}
        if isinstance(context, dict):
            project_context = ProjectContext(goal=goal)
            for key, value in context.items():
                if key in ProjectContext.__dataclass_fields__:
                    setattr(project_context, key, value)
        else:
            project_context = context

        Logger.info(f"[ScalableOrchestrator] Starting pipeline for: {goal}")
        self.event_bus.publish(PROJECT_STARTED, {"goal": goal})

        # Phase 1: CEO determines required agents
        ceo = self.registry.get("ceo")
        if not ceo:
            return ExecutionResult.failed("CEO agent not registered", duration=time.perf_counter() - started)

        ceo_result = self._run_agent_with_tracking("ceo", project_context, ceo)
        if not ceo_result.success:
            return ExecutionResult.failed(
                ceo_result.error or "CEO failed",
                data=project_context.to_dict(),
                duration=time.perf_counter() - started,
            )

        required_agents = ceo_result.output.get("required_agents", []) if isinstance(ceo_result.output, dict) else []
        project_context = ceo_result.metadata.get("context", project_context)

        # Phase 2: Execute agents in dependency order with parallel execution
        execution_result = self._execute_agent_pipeline(required_agents, project_context)

        # Phase 3: Self-improving repair loop if needed
        if self.repair_loop and project_context.errors:
            repair_summary = self._run_repair_loop(project_context)
            project_context.set_metric("repair_summary", repair_summary)

        # Finalize
        project_context.status = "completed"
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

    def _execute_agent_pipeline(self, agent_names: List[str], context: ProjectContext) -> AgentResult:
        """Execute agent pipeline with dependency-aware parallel execution."""
        if not agent_names:
            return AgentResult(agent_name="pipeline", success=True, output={"completed": []})

        # Build dependency graph
        agent_dependencies = self._build_dependencies(agent_names)
        tasks = [
            AgentTask(agent_name=name, dependencies=agent_dependencies.get(name, []))
            for name in agent_names
        ]

        def execute_task(task: AgentTask) -> AgentResult:
            agent = self.registry.get(task.agent_name)
            if not agent:
                return AgentResult(agent_name=task.agent_name, success=False, error=f"Agent not found: {task.agent_name}")

            Logger.info(f"[ScalableOrchestrator] Running agent: {task.agent_name}")
            context.current_task = task.agent_name

            try:
                result = self._run_agent_with_tracking(task.agent_name, context, agent)
                if result.success:
                    context.add_completed_task(task.agent_name)
                    self._broadcast_completion(task.agent_name, result)
                else:
                    context.add_error(result.error or f"{task.agent_name} failed")
                    Logger.error(f"[ScalableOrchestrator] {task.agent_name} failed: {result.error}")
                return result
            except Exception as exc:
                error_msg = f"{task.agent_name} error: {exc}"
                context.add_error(error_msg)
                Logger.error(f"[ScalableOrchestrator] {error_msg}")
                return AgentResult(agent_name=task.agent_name, success=False, error=error_msg)

        results = self.parallel_executor.execute(tasks, execute_task)
        successful = [r for r in results if r.success]
        Logger.info(f"[ScalableOrchestrator] Pipeline complete: {len(successful)}/{len(results)} agents succeeded")
        return results[-1] if results else AgentResult(agent_name="pipeline", success=True)

    def _build_dependencies(self, agent_names: List[str]) -> Dict[str, List[str]]:
        """Build dependency graph for agents."""
        dependencies: Dict[str, List[str]] = {}
        sequential_groups = [
            ["ceo", "requirement"],
            ["architect"],
            ["backend", "frontend", "database"],
            ["testing", "security"],
            ["deployment"],
            ["reviewer"],
            ["documentation"],
        ]

        for agent in agent_names:
            deps = []
            for group in sequential_groups:
                if agent in group:
                    for prev_agent in group[:group.index(agent)]:
                        if prev_agent in agent_names:
                            deps.append(prev_agent)
                    for prev_group in sequential_groups[:sequential_groups.index(group)]:
                        for prev_agent in prev_group:
                            if prev_agent in agent_names and prev_agent not in deps:
                                deps.append(prev_agent)
            dependencies[agent] = deps

        return dependencies

    def _run_agent_with_tracking(self, agent_name: str, context: ProjectContext, agent: Any) -> AgentResult:
        """Run an agent and track execution in history."""
        start = time.perf_counter()
        try:
            result = agent.run(context)
            duration = time.perf_counter() - start
            success = result.get("success", False) if isinstance(result, dict) else False

            # Record execution
            record = ExecutionRecord(
                execution_id=f"agent-{int(time.time() * 1000)}",
                agent_name=agent_name,
                task_type=getattr(context, "current_task", "unknown"),
                success=success,
                duration=duration,
                error=result.get("error") if isinstance(result, dict) else None,
                output_summary=str(result.get("output", ""))[:200] if isinstance(result, dict) else str(result)[:200],
            )
            self.execution_history.record(record)

            return AgentResult(
                agent_name=agent_name,
                success=success,
                output=result.get("output") if isinstance(result, dict) else result,
                error=result.get("error") if isinstance(result, dict) else str(result),
                duration=duration,
                metadata={"context": context},
            )
        except Exception as exc:
            duration = time.perf_counter() - start
            record = ExecutionRecord(
                execution_id=f"agent-{int(time.time() * 1000)}",
                agent_name=agent_name,
                task_type=getattr(context, "current_task", "unknown"),
                success=False,
                duration=duration,
                error=str(exc),
            )
            self.execution_history.record(record)
            return AgentResult(agent_name=agent_name, success=False, error=str(exc), duration=duration)

    def _broadcast_completion(self, agent_name: str, result: AgentResult):
        """Broadcast agent completion via message bus."""
        self.message_bus.broadcast(
            sender=agent_name,
            receivers=["orchestrator", "monitor"],
            message_type="AGENT_COMPLETED",
            payload=result.to_dict(),
        )

    def _run_repair_loop(self, context: ProjectContext) -> Dict[str, Any]:
        """Run self-improving repair loop on project errors."""
        if not self.repair_loop:
            return {"status": "disabled"}

        errors = [{"message": err} for err in context.errors]
        return self.repair_loop.run_repair_loop(errors, "orchestrator")

    execute = run
