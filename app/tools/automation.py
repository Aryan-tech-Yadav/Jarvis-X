"""Automation tool.

Actions: run_script, schedule, notify, workflow
"""

from __future__ import annotations

import os
import subprocess
from typing import Any, Dict, List

from app.tools.base_tool import BaseTool, ToolMetadata, ToolResult


class AutomationTool(BaseTool):
    metadata = ToolMetadata(
        name="automation",
        description="Automation operations: run scripts, schedule tasks, send notifications",
        version="1.0.0",
        author="Jarvis",
        actions=["run_script", "schedule", "notify", "workflow"],
        permissions=["system.exec", "system.schedule"],
        tags=["automation", "script", "schedule", "notify"],
    )

    def run(self, action: str = "", **kwargs) -> dict:
        if action not in self.metadata.actions:
            return ToolResult.fail(f"Unsupported action: {action}").to_dict()

        try:
            if action == "run_script":
                return self._run_script(kwargs)

            if action == "schedule":
                return self._schedule(kwargs)

            if action == "notify":
                return self._notify(kwargs)

            if action == "workflow":
                return self._workflow(kwargs)

        except Exception as exc:
            return ToolResult.fail(str(exc)).to_dict()

        return ToolResult.fail(f"Unhandled action: {action}").to_dict()

    def _run_script(self, kwargs) -> dict:
        script = kwargs.get("script") or kwargs.get("command")
        if not script:
            return ToolResult.fail("Script path or command is required").to_dict()
        cwd = kwargs.get("cwd") or kwargs.get("base_path") or os.getcwd()
        if os.path.isfile(script):
            cmd = [script]
        elif isinstance(script, str):
            cmd = script if isinstance(script, list) else script.split()
        else:
            cmd = list(script)
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
        if result.returncode == 0:
            return ToolResult.ok(output=result.stdout.strip()).to_dict()
        return ToolResult.fail(result.stderr.strip()).to_dict()

    def _schedule(self, kwargs) -> dict:
        task = kwargs.get("task")
        when = kwargs.get("when") or kwargs.get("cron")
        if not task or not when:
            return ToolResult.fail("Task and schedule are required").to_dict()
        return ToolResult.ok(output=f"Scheduled: {task} at {when}").to_dict()

    def _notify(self, kwargs) -> dict:
        message = kwargs.get("message") or kwargs.get("text")
        if not message:
            return ToolResult.fail("Message is required").to_dict()
        title = kwargs.get("title", "Jarvis Notification")
        return ToolResult.ok(output=f"Notification: {title} - {message}").to_dict()

    def _workflow(self, kwargs) -> dict:
        steps = kwargs.get("steps") or kwargs.get("workflow", [])
        return ToolResult.ok(output=f"Workflow defined with {len(steps)} steps").to_dict()
