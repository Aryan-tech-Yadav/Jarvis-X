"""Project tool.

Actions: create, modify, analyze
"""

from __future__ import annotations

from typing import Any, Dict

from app.tools.base_tool import BaseTool, ToolMetadata, ToolResult


class ProjectTool(BaseTool):
    metadata = ToolMetadata(
        name="project",
        description="Project operations: create, modify, analyze projects",
        version="1.0.0",
        author="Jarvis",
        actions=["create", "modify", "analyze"],
        permissions=["filesystem.read", "filesystem.write"],
        tags=["project", "workspace", "engineering"],
    )

    def __init__(self, manager=None):
        super().__init__()
        self.manager = manager

    def run(self, action: str = "", **kwargs) -> dict:
        if action not in self.metadata.actions:
            return ToolResult.fail(f"Unsupported action: {action}").to_dict()

        if self.manager is None:
            return ToolResult.fail("Project manager not configured").to_dict()

        try:
            if action == "create":
                result = self.manager.create_project(kwargs.get("request", ""))
                return ToolResult.ok(output=result, artifacts=[result] if isinstance(result, str) else []).to_dict()

            if action == "modify":
                project = kwargs.get("current_project") or kwargs.get("project")
                if not project:
                    return ToolResult.fail("No current project").to_dict()
                result = self.manager.modify_project(project, kwargs.get("request", ""))
                return ToolResult.ok(output=result).to_dict()

            if action == "analyze":
                project = kwargs.get("current_project") or kwargs.get("project")
                if not project:
                    return ToolResult.fail("No current project").to_dict()
                result = self.manager.analyze_project(project)
                return ToolResult.ok(output=result).to_dict()

        except Exception as exc:
            return ToolResult.fail(str(exc)).to_dict()

        return ToolResult.fail(f"Unhandled action: {action}").to_dict()
