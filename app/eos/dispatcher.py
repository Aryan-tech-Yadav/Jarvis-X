"""Capability-aware agent dispatcher."""

from __future__ import annotations

from typing import Any

from app.eos.executor import AgentExecutor
from app.eos.registry import AgentRegistry
from app.eos.result import AgentResult


class Dispatcher:
    def __init__(self, registry: AgentRegistry, executor: AgentExecutor | None = None):
        self.registry = registry
        self.executor = executor or AgentExecutor()

    def dispatch(self, task: Any) -> AgentResult:
        agent = self.registry.find(task)
        requested = getattr(task, "capability", "") or getattr(task, "agent", "")
        if isinstance(task, dict):
            requested = task.get("capability") or task.get("agent") or task.get("type") or ""
        if agent is None:
            return AgentResult(False, error=f"No agent available for task: {requested or task}", agent=str(requested))
        name = self.registry._name_for(agent)
        if not getattr(agent, "enabled", True):
            return AgentResult(False, error=f"Agent is disabled: {name}", agent=name)
        health_check = getattr(agent, "health_check", None)
        if callable(health_check) and not health_check():
            return AgentResult(False, error=f"Agent is unhealthy: {name}", agent=name)
        return self.executor.execute(agent, task)
