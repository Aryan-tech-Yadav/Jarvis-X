"""Search tool.

Actions: search, find, grep
"""

from __future__ import annotations

import os
from typing import Any, Dict

from app.tools.base_tool import BaseTool, ToolMetadata, ToolResult


class SearchTool(BaseTool):
    metadata = ToolMetadata(
        name="search",
        description="Search files and content within directories",
        version="1.0.0",
        author="Jarvis",
        actions=["search", "find", "grep"],
        permissions=["filesystem.read"],
        tags=["search", "filesystem", "grep"],
    )

    SKIPPED_DIRECTORIES = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "node_modules", ".tox"}

    def run(self, action: str = "", **kwargs) -> dict:
        if action not in self.metadata.actions:
            return ToolResult.fail(f"Unsupported action: {action}").to_dict()

        root = kwargs.get("path") or kwargs.get("base_path") or os.getcwd()
        query = kwargs.get("query") or kwargs.get("term")
        if not query:
            return ToolResult.fail("Search query is required").to_dict()

        try:
            results = []
            for current_root, directories, files in os.walk(root):
                directories[:] = [d for d in directories if d not in self.SKIPPED_DIRECTORIES]
                for file_name in files:
                    file_path = os.path.join(current_root, file_name)
                    try:
                        with open(file_path, "r", encoding="utf-8") as handle:
                            contents = handle.read()
                    except (OSError, UnicodeDecodeError):
                        continue
                    if query in contents:
                        results.append(file_path)
            return ToolResult.ok(output=results).to_dict()
        except OSError as exc:
            return ToolResult.fail(str(exc)).to_dict()

        return ToolResult.fail(f"Unhandled action: {action}").to_dict()
