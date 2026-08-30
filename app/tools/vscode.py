"""VS Code tool.

Actions: open, list_files, search_files
"""

from __future__ import annotations

import os
import subprocess
from typing import Any, Dict, List

from app.tools.base_tool import BaseTool, ToolMetadata, ToolResult


class VSCodeTool(BaseTool):
    metadata = ToolMetadata(
        name="vscode",
        description="Visual Studio Code operations: open folders, search files, run extensions",
        version="1.0.0",
        author="Jarvis",
        actions=["open", "list_files", "search"],
        permissions=["filesystem.read", "system.exec"],
        tags=["vscode", "editor", "ide", "code"],
    )

    def run(self, action: str = "", **kwargs) -> dict:
        if action not in self.metadata.actions:
            return ToolResult.fail(f"Unsupported action: {action}").to_dict()

        try:
            if action == "open":
                path = kwargs.get("path") or kwargs.get("folder") or kwargs.get("base_path") or os.getcwd()
                self._open_vscode(path)
                return ToolResult.ok(output=f"Opened VS Code: {path}").to_dict()

            if action == "list_files":
                path = kwargs.get("path") or kwargs.get("base_path") or os.getcwd()
                return ToolResult.ok(output=os.listdir(path)).to_dict()

            if action == "search":
                query = kwargs.get("query") or kwargs.get("term")
                path = kwargs.get("path") or kwargs.get("base_path") or os.getcwd()
                if not query:
                    return ToolResult.fail("Search query is required").to_dict()
                results = []
                for root, _, files in os.walk(path):
                    for fname in files:
                        if query.lower() in fname.lower():
                            results.append(os.path.join(root, fname))
                return ToolResult.ok(output=results).to_dict()

        except Exception as exc:
            return ToolResult.fail(str(exc)).to_dict()

        return ToolResult.fail(f"Unhandled action: {action}").to_dict()

    def _open_vscode(self, path: str):
        try:
            subprocess.run(["code", path], capture_output=True, check=False)
        except (OSError, FileNotFoundError):
            pass
