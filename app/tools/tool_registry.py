"""Tool registry.

Central registry for all tools.
Supports:
  - Registration with metadata
  - Capability-based search
  - Permission-aware dispatch
  - Dynamic discovery
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.tools.base_tool import BaseTool, ToolMetadata


class ToolRegistry:
    """Central registry for Jarvis-X tools."""

    def __init__(self, permission_manager=None):
        self._tools: Dict[str, BaseTool] = {}
        self._permission_manager = permission_manager

    def register(self, tool_or_name, tool=None) -> str:
        """Register a tool.

        Supports both:
          register(tool_instance)
          register(name, tool_instance)
        """
        if tool is None:
            tool = tool_or_name
            if not isinstance(tool, BaseTool):
                raise TypeError(f"Tool must inherit from BaseTool, got {type(tool).__name__}")
            name = tool.metadata.name
            if not name or not name.strip():
                raise ValueError("Tool metadata.name cannot be empty")
            name = name.strip()
            if name in self._tools:
                raise ValueError(f"Tool already registered: {name}")
            self._tools[name] = tool
            return name

        # Legacy: register(name, tool)
        if not isinstance(tool, BaseTool):
            raise TypeError(f"Tool must inherit from BaseTool, got {type(tool).__name__}")
        name = str(tool_or_name).strip()
        if not name:
            raise ValueError("Tool name cannot be empty")
        if name in self._tools:
            raise ValueError(f"Tool already registered: {name}")
        # Update tool metadata with the provided name if it differs
        if tool.metadata.name != name:
            tool.metadata.name = name
        self._tools[name] = tool
        return name

    def unregister(self, name: str) -> Optional[BaseTool]:
        return self._tools.pop(name.strip(), None)

    def get(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name.strip())

    def list(self) -> List[BaseTool]:
        return list(self._tools.values())

    def names(self) -> List[str]:
        return list(self._tools.keys())

    def metadata(self) -> List[Dict[str, Any]]:
        return [tool.metadata.to_dict() for tool in self._tools.values() if tool.metadata]

    def search(self, query: str) -> List[BaseTool]:
        """Search tools by name, description, or tags."""
        terms = str(query).casefold().split()
        if not terms:
            return self.list()
        results = []
        for tool in self._tools.values():
            meta = tool.metadata
            haystack = f"{meta.name} {meta.description} {' '.join(meta.tags)} {' '.join(meta.actions)}".casefold()
            if any(term in haystack for term in terms):
                results.append(tool)
        return results

    def find_by_action(self, action: str) -> List[BaseTool]:
        """Find tools that support a specific action."""
        return [tool for tool in self._tools.values() if tool.can_handle(action)]

    def find_by_permission(self, permission: str) -> List[BaseTool]:
        """Find tools that require a specific permission."""
        return [tool for tool in self._tools.values() if permission in (tool.metadata.permissions or [])]

    def execute(self, tool_name: str, action: Optional[str] = None,
                context: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """Execute a tool with fail-closed checks for dangerous permissions."""
        tool = self.get(tool_name)
        if tool is None:
            return {"success": False, "error": f"Tool not registered: {tool_name}"}

        permissions = list(
            getattr(getattr(tool, "metadata", None), "permissions", None) or []
        )

        if self._permission_manager is not None:
            try:
                perm = self._permission_manager.check(
                    tool_name, action or "", permissions
                )
                if not perm.allowed:
                    return {
                        "success": False,
                        "error": f"Permission denied: {perm.reason}",
                    }
            except Exception as exc:
                return {
                    "success": False,
                    "error": f"Permission check failed; execution blocked: {exc}",
                }
        else:
            from app.tools.permission_manager import PermissionManager

            dangerous = (
                set(permissions) & PermissionManager.DANGEROUS_PERMISSIONS
            )
            if dangerous:
                return {
                    "success": False,
                    "error": (
                        "Permission manager unavailable; refusing dangerous "
                        f"operation: {', '.join(sorted(dangerous))}"
                    ),
                }

        try:
            return tool.execute(action, context=context, **kwargs)
        except Exception as exc:
            return {"success": False, "error": str(exc)}
