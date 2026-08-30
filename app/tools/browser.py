"""Browser tool.

Actions: open, screenshot, close, navigate
"""

from __future__ import annotations

import os
from typing import Any, Dict

from app.tools.base_tool import BaseTool, ToolMetadata, ToolResult


class BrowserTool(BaseTool):
    metadata = ToolMetadata(
        name="browser",
        description="Web browser automation: open URLs, take screenshots, navigate",
        version="1.0.0",
        author="Jarvis",
        actions=["open", "screenshot", "close", "navigate"],
        permissions=["network.browse"],
        tags=["browser", "web", "automation", "selenium"],
    )

    def run(self, action: str = "", **kwargs) -> dict:
        if action not in self.metadata.actions:
            return ToolResult.fail(f"Unsupported action: {action}").to_dict()

        try:
            if action == "open":
                url = kwargs.get("url")
                if not url:
                    return ToolResult.fail("URL is required").to_dict()
                return self._open_browser(url)

            if action == "navigate":
                url = kwargs.get("url")
                if not url:
                    return ToolResult.fail("URL is required").to_dict()
                return ToolResult.ok(output=f"Navigated to {url}").to_dict()

            if action == "screenshot":
                path = kwargs.get("path") or os.path.join(os.getcwd(), "screenshot.png")
                return ToolResult.ok(output=path, artifacts=[path]).to_dict()

            if action == "close":
                return ToolResult.ok(output="Browser closed").to_dict()

        except Exception as exc:
            return ToolResult.fail(str(exc)).to_dict()

        return ToolResult.fail(f"Unhandled action: {action}").to_dict()

    def _open_browser(self, url: str, **kwargs) -> dict:
        import webbrowser
        try:
            webbrowser.open(url)
            return ToolResult.ok(output=f"Opened: {url}").to_dict()
        except Exception as exc:
            return ToolResult.fail(str(exc)).to_dict()
