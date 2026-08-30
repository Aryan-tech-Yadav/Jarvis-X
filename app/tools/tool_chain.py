"""Tool chaining for multi-step workflows.

Example:
    chain = ToolChain()
    chain.add("git", "clone", repo="...")
    chain.add("vscode", "open", path=".")
    chain.add("python", "run", file_name="main.py")
    chain.execute_all(registry)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.tools.base_tool import BaseTool, ToolResult


@dataclass
class ChainStep:
    """Single step in a tool chain."""

    tool_name: str
    action: str = ""
    params: Dict[str, Any] = field(default_factory=dict)
    on_failure: str = "stop"  # stop | continue | retry
    max_retries: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "action": self.action,
            "params": dict(self.params),
            "on_failure": self.on_failure,
            "max_retries": self.max_retries,
        }


@dataclass
class ChainResult:
    """Result of executing a tool chain."""

    success: bool
    steps_executed: int
    total_steps: int
    results: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    duration: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "steps_executed": self.steps_executed,
            "total_steps": self.total_steps,
            "results": list(self.results),
            "errors": list(self.errors),
            "duration": self.duration,
        }


class ToolChain:
    """Chain multiple tool executions together."""

    def __init__(self, registry=None, permission_manager=None):
        self._steps: List[ChainStep] = []
        self.registry = registry
        self.permission_manager = permission_manager

    def add(self, tool_name: str, action: str = "", params: Optional[Dict[str, Any]] = None,
            on_failure: str = "stop", max_retries: int = 0) -> ChainStep:
        """Add a step to the chain."""
        step = ChainStep(
            tool_name=tool_name,
            action=action,
            params=params or {},
            on_failure=on_failure,
            max_retries=max_retries,
        )
        self._steps.append(step)
        return step

    def execute_all(self, registry=None) -> ChainResult:
        """Execute all steps in the chain."""
        registry = registry or self.registry
        if registry is None:
            return ChainResult(success=False, steps_executed=0, total_steps=len(self._steps),
                               errors=["No tool registry provided"])

        started = time.perf_counter()
        results: List[Dict[str, Any]] = []
        errors: List[str] = []
        executed = 0

        for step in self._steps:
            tool = registry.get(step.tool_name)
            if tool is None:
                errors.append(f"Tool not found: {step.tool_name}")
                if step.on_failure == "stop":
                    break
                continue

            if self.permission_manager:
                perm = self.permission_manager.check(
                    step.tool_name, step.action, getattr(tool, "permissions", [])
                )
                if not perm.allowed:
                    errors.append(f"Permission denied: {step.tool_name}.{step.action}: {perm.reason}")
                    if step.on_failure == "stop":
                        break
                    continue

            attempt = 0
            last_result = None
            while attempt <= max(step.max_retries, 0):
                attempt += 1
                try:
                    last_result = tool.execute(step.action, context=step.params, **step.params)
                    if isinstance(last_result, dict) and last_result.get("success"):
                        break
                except Exception as exc:
                    last_result = {"success": False, "error": str(exc)}

            if isinstance(last_result, dict) and last_result.get("success"):
                results.append(last_result)
                executed += 1
            else:
                error_msg = (last_result or {}).get("error", "Unknown error") if isinstance(last_result, dict) else "Unknown error"
                errors.append(f"{step.tool_name}.{step.action}: {error_msg}")
                if step.on_failure == "stop":
                    break

        return ChainResult(
            success=len(errors) == 0 and executed == len(self._steps),
            steps_executed=executed,
            total_steps=len(self._steps),
            results=results,
            errors=errors,
            duration=time.perf_counter() - started,
        )

    def steps(self) -> List[Dict[str, Any]]:
        return [s.to_dict() for s in self._steps]

    def clear(self):
        self._steps.clear()
