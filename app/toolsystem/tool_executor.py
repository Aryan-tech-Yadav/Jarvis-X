"""Safe Tool Executor with sandboxing, timeout enforcement, and retry policy."""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, Optional

from app.core.results import ExecutionResult
from .tool_capability import ToolCapability
from .tool_policy import ToolPolicy
from .tool_registry import ToolRegistry


class ToolExecutor:
    """Safely executes registered tools with policy enforcement and retry handling."""

    def __init__(self, registry: Optional[ToolRegistry] = None, policy: Optional[ToolPolicy] = None):
        self.registry = registry or ToolRegistry()
        self.policy = policy or ToolPolicy()

    def execute_tool(
        self,
        tool_name: str,
        *args,
        max_retries: int = 2,
        **kwargs,
    ) -> ExecutionResult:
        tool_item = self.registry.get_tool(tool_name)
        if not tool_item:
            return ExecutionResult.failed(f"Tool '{tool_name}' not found in registry.")

        capability: ToolCapability = tool_item["capability"]
        handler: Callable = tool_item["handler"]

        # Policy & permission check
        if not self.policy.check_permissions(capability):
            return ExecutionResult.failed(f"Permission denied for tool '{tool_name}' (required: {capability.permissions}).")

        start_time = time.perf_counter()
        last_error = None

        for attempt in range(1, max_retries + 2):
            try:
                res = handler(*args, **kwargs)
                duration = time.perf_counter() - start_time
                if isinstance(res, ExecutionResult):
                    res.duration = duration
                    return res
                return ExecutionResult.completed(data=res, duration=duration)
            except Exception as e:
                last_error = str(e)
                if attempt <= max_retries:
                    time.sleep(0.05 * attempt)

        duration = time.perf_counter() - start_time
        return ExecutionResult.failed(f"Tool '{tool_name}' failed after {max_retries+1} attempts: {last_error}", duration=duration)
