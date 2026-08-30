"""Terminal tool.

Actions: run, exec
"""

from __future__ import annotations

import os
import subprocess

from app.tools.base_tool import BaseTool, ToolMetadata, ToolResult


class TerminalTool(BaseTool):
    metadata = ToolMetadata(
        name="terminal",
        description="Terminal command execution",
        version="1.0.0",
        author="Jarvis",
        actions=["run", "exec"],
        permissions=["system.exec", "terminal"],
        tags=["terminal", "shell", "cli"],
    )

    FORBIDDEN_PATTERNS = (
        "rm -rf /",
        "del /f /s /q c:\\",
        "shutdown",
        "format",
        "sudo rm",
        "chmod -R 777 /",
        "rmdir /s /q c:\\",
    )

    def run(self, action: str = "", **kwargs) -> dict:
        if action not in self.metadata.actions:
            return ToolResult.fail(f"Unsupported action: {action}").to_dict()

        command = kwargs.get("command")
        if not command:
            return ToolResult.fail("Command is required").to_dict()

        command_text = str(command).lower()
        for pattern in self.FORBIDDEN_PATTERNS:
            if pattern in command_text:
                return ToolResult.fail(f"Blocked dangerous command: {command}",
                                       metadata={"blocked_pattern": pattern}).to_dict()

        cwd = kwargs.get("cwd") or kwargs.get("base_path") or os.getcwd()
        try:
            completed = subprocess.run(
                command,
                cwd=cwd,
                shell=isinstance(command, str),
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as exc:
            return ToolResult.fail(str(exc)).to_dict()

        output = (completed.stdout or "").strip()
        error = (completed.stderr or "").strip()
        if completed.returncode == 0:
            return ToolResult.ok(output=output, metadata={"returncode": completed.returncode}).to_dict()
        return ToolResult.fail(error or "Command failed", output=output,
                                metadata={"returncode": completed.returncode}).to_dict()
