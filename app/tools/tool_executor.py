"""Tool executor.

Dispatches tool execution through the registry.
No hardcoded if-else chains.
"""

from __future__ import annotations

from time import perf_counter
from typing import Any, Dict, Optional

from app.tools.tool_result import ToolResult


class ToolExecutor:
    """Execute tools via registry dispatch."""

    def __init__(self, registry=None, permission_manager=None):
        self.registry = registry
        self.permission_manager = permission_manager

    def execute(self, tool_name: str, base_path: Optional[str] = None,
                action: Optional[str] = None, context: Optional[Dict[str, Any]] = None,
                **kwargs) -> Dict[str, Any]:
        """Execute a tool through the registry."""
        started = perf_counter()
        if context is None:
            context = {}
        if base_path is not None:
            context.setdefault("base_path", base_path)

        if self.registry is None:
            result = ToolResult.fail("No tool registry configured")
            result.duration = perf_counter() - started
            return result.to_dict()

        result = self.registry.execute(tool_name, action=action, context=context, **kwargs)
        normalized = ToolResult.from_value(result)
        normalized.duration = perf_counter() - started
        normalized.metadata.setdefault("tool", tool_name)
        return normalized.to_dict()

    def execute_chain(self, chain, registry=None) -> Dict[str, Any]:
        """Execute a ToolChain."""
        from app.tools.tool_chain import ToolChain
        registry = registry or self.registry
        if isinstance(chain, ToolChain):
            result = chain.execute_all(registry)
            return result.to_dict()
        return ToolResult.fail("Invalid chain object").to_dict()
