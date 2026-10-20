"""Dependency-aware workflow facade for multi-agent runs."""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from app.agents.parallel_executor import AgentResult, AgentTask, ParallelAgentExecutor
from app.orchestrator.task_graph import TaskGraph


class WorkflowEngine:
    """Execute a task graph through a supplied agent registry."""

    def __init__(self, registry: Any, max_workers: int = 4):
        self.registry = registry
        self.executor = ParallelAgentExecutor(max_workers=max_workers)

    def run(self, graph: TaskGraph, context: Any) -> Dict[str, AgentResult]:
        tasks = [
            AgentTask(
                agent_name=node.id,
                task=context,
                dependencies=list(node.dependencies),
                metadata={"agent": node.agent},
            )
            for node in graph.nodes()
        ]

        def execute(task: AgentTask) -> AgentResult:
            name = task.metadata.get("agent") or task.agent_name
            agent = self.registry.get(name) or self.registry.find(name)
            if agent is None:
                return AgentResult(task.agent_name, False, error=f"Agent not registered: {name}")
            result = agent.execute(context)
            success = result.get("success", False) if isinstance(result, dict) else False
            return AgentResult(task.agent_name, success, output=result, error=None if success else str(result))

        return {result.agent_name: result for result in self.executor.execute(tasks, execute)}
