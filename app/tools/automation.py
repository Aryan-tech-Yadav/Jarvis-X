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

    DEFAULT_TIMEOUT = 30
    MAX_OUTPUT_CHARS = 20000

    def _truncate(self, value):
        value = value or ""
        if len(value) > self.MAX_OUTPUT_CHARS:
            return value[:self.MAX_OUTPUT_CHARS] + "\n...[output truncated]"
        return value

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
        if not isinstance(cwd, str) or not os.path.isdir(cwd):
            return ToolResult.fail("Working directory must be an existing directory").to_dict()

        if isinstance(script, str):
            cmd = [script] if os.path.isfile(script) else script.split()
        elif isinstance(script, (list, tuple)) and script:
            if not all(isinstance(arg, str) and arg for arg in script):
                return ToolResult.fail("Script arguments must be non-empty strings").to_dict()
            cmd = list(script)
        else:
            return ToolResult.fail("Script must be a path or a non-empty command").to_dict()

        try:
            timeout = float(kwargs.get("timeout", self.DEFAULT_TIMEOUT))
            if not 1 <= timeout <= 300:
                return ToolResult.fail("Timeout must be between 1 and 300 seconds").to_dict()

            import tempfile
            with tempfile.TemporaryFile(mode="w+t", encoding="utf-8") as stdout_file, \
                 tempfile.TemporaryFile(mode="w+t", encoding="utf-8") as stderr_file:
                result = subprocess.run(
                    cmd, cwd=cwd, stdout=stdout_file, stderr=stderr_file, text=True,
                    timeout=timeout, shell=False, check=False,
                )
                stdout_file.seek(0)
                stderr_file.seek(0)
                output = self._truncate(stdout_file.read(self.MAX_OUTPUT_CHARS + 1).strip())
                error = self._truncate(stderr_file.read(self.MAX_OUTPUT_CHARS + 1).strip())
        except subprocess.TimeoutExpired:
            return ToolResult.fail(f"Script timed out after {timeout:g} seconds").to_dict()
        except (OSError, ValueError, TypeError) as exc:
            return ToolResult.fail(str(exc)).to_dict()
        if result.returncode == 0:
            return ToolResult.ok(output=output).to_dict()
        return ToolResult.fail(error or "Script failed", output=output).to_dict()

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
