"""Memory tool.

Actions: remember, recall, forget, list, clear
"""

from __future__ import annotations

from typing import Any, Dict, List

from app.tools.base_tool import BaseTool, ToolMetadata, ToolResult


class MemoryTool(BaseTool):
    metadata = ToolMetadata(
        name="memory",
        description="Memory operations: store, retrieve, and manage knowledge",
        version="1.0.0",
        author="Jarvis",
        actions=["remember", "recall", "forget", "list", "clear"],
        permissions=["memory.read", "memory.write"],
        tags=["memory", "knowledge", "storage"],
    )

    def __init__(self, knowledge_manager=None, semantic_memory=None):
        super().__init__()
        self.km = knowledge_manager
        self.sm = semantic_memory
        self._local_store: Dict[str, Any] = {}

    def run(self, action: str = "", **kwargs) -> dict:
        if action not in self.metadata.actions:
            return ToolResult.fail(f"Unsupported action: {action}").to_dict()

        try:
            if action == "remember":
                key = kwargs.get("key") or kwargs.get("id")
                value = kwargs.get("value") or kwargs.get("content")
                if not key or value is None:
                    return ToolResult.fail("Key and value are required").to_dict()
                self._local_store[str(key)] = value
                if self.km:
                    self.km.add(str(key), str(value))
                if self.sm:
                    self.sm.add(str(key), str(value))
                return ToolResult.ok(output=f"Remembered: {key}").to_dict()

            if action == "recall":
                key = kwargs.get("key") or kwargs.get("id")
                if key:
                    val = self._local_store.get(str(key))
                    if val is None and self.km:
                        val = self.km.get(str(key))
                    return ToolResult.ok(output=val).to_dict()
                limit = kwargs.get("limit", 10)
                return ToolResult.ok(output=list(self._local_store.items())[:limit]).to_dict()

            if action == "forget":
                key = kwargs.get("key") or kwargs.get("id")
                if key:
                    self._local_store.pop(str(key), None)
                    return ToolResult.ok(output=f"Forgot: {key}").to_dict()
                self._local_store.clear()
                return ToolResult.ok(output="Memory cleared").to_dict()

            if action == "list":
                return ToolResult.ok(output=list(self._local_store.keys())).to_dict()

            if action == "clear":
                self._local_store.clear()
                return ToolResult.ok(output="Memory cleared").to_dict()

        except Exception as exc:
            return ToolResult.fail(str(exc)).to_dict()

        return ToolResult.fail(f"Unhandled action: {action}").to_dict()
