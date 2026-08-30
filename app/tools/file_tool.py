"""File tool.

Legacy wrapper around FileSystemTool.
Kept for backward compatibility.
"""

from __future__ import annotations

import os

from app.tools.base_tool import BaseTool, ToolMetadata, ToolResult


class FileTool(BaseTool):
    metadata = ToolMetadata(
        name="file",
        description="Legacy file operations: read, write, list",
        version="1.0.0",
        author="Jarvis",
        actions=["read", "write", "list", "delete", "exists"],
        permissions=["filesystem.read", "filesystem.write"],
        tags=["filesystem", "file", "legacy"],
    )

    def run(self, action: str = "", **kwargs) -> dict:
        if action not in self.metadata.actions:
            return ToolResult.fail(f"Unsupported action: {action}").to_dict()

        path = kwargs.get("path") or kwargs.get("file_path")
        if not path and action not in {"list"}:
            return ToolResult.fail("File path is required").to_dict()

        try:
            if action == "read":
                with open(path, "r", encoding="utf-8") as f:
                    return ToolResult.ok(output=f.read()).to_dict()

            if action == "write":
                content = kwargs.get("content", "")
                parent = os.path.dirname(path)
                if parent:
                    os.makedirs(parent, exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                return ToolResult.ok(output=path, artifacts=[path]).to_dict()

            if action == "list":
                target = path or "."
                return ToolResult.ok(output=os.listdir(target)).to_dict()

            if action == "exists":
                return ToolResult.ok(output=os.path.exists(path)).to_dict()

            if action == "delete":
                os.remove(path)
                return ToolResult.ok(output=path).to_dict()

        except (OSError, UnicodeDecodeError) as exc:
            return ToolResult.fail(str(exc)).to_dict()

        return ToolResult.fail(f"Unhandled action: {action}").to_dict()
