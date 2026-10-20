"""Tool chaining for multi-step workflows."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.tools.base_tool import BaseTool, ToolResult
from app.tools.permission_manager import PermissionManager


@dataclass
class ChainStep:
    """Single step in a tool chain."""

    tool_name: str
    action: str = ""
    params: Dict[str, Any] = field(default_factory=dict)
    on_failure: str = "stop"
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
    """Chain multiple tool executions with permission enforcement."""

    def __init__(self, registry=None, permission_manager=None):
        self._steps: List[ChainStep] = []
        self.registry = registry
        self.permission_manager = (
            permission_manager
            or getattr(registry, "_permission_manager", None)
        )

    def add(
        self,
        tool_name: str,
        action: str = "",
        params: Optional[Dict[str, Any]] = None,
        on_failure: str = "stop",
        max_retries: int = 0,
    ) -> ChainStep:
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
        """Execute chain steps after checking required permissions."""
        registry = registry or self.registry
        if registry is None:
            return ChainResult(
                success=False,
                steps_executed=0,
                total_steps=len(self._steps),
                errors=["No tool registry provided"],
            )

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

            metadata = getattr(tool, "metadata", None)
            permissions = list(getattr(metadata, "permissions", None) or [])

            # Resolve a manager from the active registry if one was supplied
            # to execute_all() rather than to the constructor.
            manager = (
                self.permission_manager
                or getattr(registry, "_permission_manager", None)
            )

            if manager is not None:
                try:
                    permission_result = manager.check(
                        step.tool_name, step.action, permissions
                    )
                    allowed = bool(
                        getattr(permission_result, "allowed", False)
                    )
                    reason = getattr(
                        permission_result, "reason", "Permission denied"
                    )
                except Exception as exc:
                    allowed = False
                    reason = f"Permission check failed: {exc}"

                if not allowed:
                    errors.append(
                        f"Permission denied: {step.tool_name}."
                        f"{step.action}: {reason}"
                    )
                    if step.on_failure == "stop":
                        break
                    continue
            else:
                dangerous_permissions = (
                    set(permissions)
                    & PermissionManager.DANGEROUS_PERMISSIONS
                )
                if dangerous_permissions:
                    dangerous = ", ".join(sorted(dangerous_permissions))
                    errors.append(
                        "Permission manager unavailable; refusing "
                        f"dangerous operation {step.tool_name}."
                        f"{step.action}: {dangerous}"
                    )
                    if step.on_failure == "stop":
                        break
                    continue

            # Retry only when explicitly requested. Each retry may repeat
            # side effects, so callers should opt in carefully.
            attempt = 0
            last_result = None

            while attempt <= max(step.max_retries, 0):
                attempt += 1
                try:
                    last_result = tool.execute(
                        step.action,
                        context=step.params,
                        **step.params,
                    )
                except Exception as exc:
                    last_result = {"success": False, "error": str(exc)}

                if (
                    isinstance(last_result, dict)
                    and last_result.get("success")
                ):
                    break

            if (
                isinstance(last_result, dict)
                and last_result.get("success")
            ):
                results.append(last_result)
                executed += 1
            else:
                if isinstance(last_result, dict):
                    error_msg = last_result.get("error", "Unknown error")
                else:
                    error_msg = "Unknown error"

                errors.append(
                    f"{step.tool_name}.{step.action}: {error_msg}"
                )
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
        return [step.to_dict() for step in self._steps]

    def clear(self):
        self._steps.clear()
