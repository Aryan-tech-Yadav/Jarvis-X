"""Autonomous Tool Selector mapping task descriptions to optimal tools."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .tool_capability import ToolCapability
from .tool_registry import ToolRegistry


class ToolSelector:
    """Matches task intent, keywords, and constraints to the most suitable registered tool."""

    INTENT_KEYWORD_MAP = {
        "docker": ["docker", "container", "dockerfile", "compose", "image"],
        "git": ["git", "commit", "branch", "repo", "vcs", "push", "tag"],
        "database": ["database", "sql", "schema", "table", "migration", "query", "postgres", "sqlite"],
        "python": ["python", "test", "pytest", "unittest", "script", "code", "run"],
        "filesystem": ["file", "directory", "folder", "write", "read", "save", "path"],
        "terminal": ["shell", "terminal", "command", "exec", "cli", "bash", "powershell"],
    }

    def __init__(self, registry: Optional[ToolRegistry] = None):
        self.registry = registry or ToolRegistry()

    def select_tool_for_task(self, task_description: str) -> Optional[ToolCapability]:
        desc_lower = task_description.lower()

        # Score registered tools
        best_tool_name = None
        best_score = 0

        for tool_name, keywords in self.INTENT_KEYWORD_MAP.items():
            score = sum(1 for kw in keywords if kw in desc_lower)
            if score > best_score:
                best_score = score
                best_tool_name = tool_name

        if not best_tool_name or best_score == 0:
            best_tool_name = "filesystem"  # Default safe tool

        tool_item = self.registry.get_tool(best_tool_name)
        return tool_item["capability"] if tool_item else None
