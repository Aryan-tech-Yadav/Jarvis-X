"""Python tool.

Actions: run, exec, script
"""

from __future__ import annotations

import os
import subprocess
import sys

from app.tools.base_tool import BaseTool, ToolMetadata, ToolResult


class PythonTool(BaseTool):
    metadata = ToolMetadata(
        name="python",
        description="Python execution: run scripts, execute code",
        version="1.0.0",
        author="Jarvis",
        actions=["run", "exec", "script"],
        permissions=["system.exec"],
        tags=["python", "script", "code"],
    )

    def run(self, action: str = "", **kwargs) -> dict:
        if action not in self.metadata.actions:
            return ToolResult.fail(f"Unsupported action: {action}").to_dict()

        code = kwargs.get("code")
        file_name = kwargs.get("file_name") or kwargs.get("path")
        if code is None and not file_name:
            return ToolResult.fail("Python code or file name is required").to_dict()

        cwd = kwargs.get("cwd") or kwargs.get("base_path") or os.getcwd()

        try:
            if code is not None:
                command = [sys.executable, "-c", code]
            else:
                command = [sys.executable, file_name]

            completed = subprocess.run(
                command,
                cwd=cwd,
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
        return ToolResult.fail(error or "Execution failed", output=output,
                                metadata={"returncode": completed.returncode}).to_dict()
