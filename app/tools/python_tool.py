"""Python tool.

Actions: run, exec, script
"""

from __future__ import annotations

import math
import os
import subprocess
import sys
from pathlib import Path

from app.tools.base_tool import BaseTool, ToolMetadata, ToolResult
from app.tools.process_utils import run_bounded


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

    DEFAULT_TIMEOUT = 30
    MAX_TIMEOUT = 300
    MAX_OUTPUT_CHARS = 20000

    def run(self, action: str = "", **kwargs) -> dict:
        if action not in self.metadata.actions:
            return ToolResult.fail(
                f"Unsupported action: {action}"
            ).to_dict()

        code = kwargs.get("code")
        file_name = kwargs.get("file_name") or kwargs.get("path")
        if code is None and not file_name:
            return ToolResult.fail(
                "Python code or file name is required"
            ).to_dict()

        cwd = kwargs.get("cwd") or kwargs.get("base_path") or os.getcwd()

        try:
            workspace = Path(cwd).expanduser().resolve(strict=True)
            if not workspace.is_dir():
                return ToolResult.fail(
                    "Workspace must be an existing directory"
                ).to_dict()

            raw_timeout = kwargs.get("timeout", self.DEFAULT_TIMEOUT)
            timeout = float(raw_timeout)

            if not math.isfinite(timeout) or not 1 <= timeout <= self.MAX_TIMEOUT:
                return ToolResult.fail(
                    f"Timeout must be between 1 and {self.MAX_TIMEOUT} seconds"
                ).to_dict()

            if code is not None:
                if not isinstance(code, str):
                    return ToolResult.fail(
                        "Python code must be a string"
                    ).to_dict()
                command = [sys.executable, "-c", code]
            else:
                candidate = Path(file_name).expanduser()
                if not candidate.is_absolute():
                    candidate = workspace / candidate

                script_path = candidate.resolve(strict=True)

                if not script_path.is_file():
                    return ToolResult.fail(
                        "Python script must be an existing file"
                    ).to_dict()

                if not script_path.is_relative_to(workspace):
                    return ToolResult.fail(
                        "Python script must be inside the workspace"
                    ).to_dict()

                command = [sys.executable, str(script_path)]

            completed = run_bounded(
                command,
                max_output_chars=self.MAX_OUTPUT_CHARS,
                cwd=str(workspace),
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )

        except subprocess.TimeoutExpired:
            return ToolResult.fail(
                f"Python execution timed out after {timeout:g} seconds"
            ).to_dict()
        except (OSError, ValueError, TypeError, RuntimeError) as exc:
            return ToolResult.fail(str(exc)).to_dict()

        output = (completed.stdout or "").strip()
        error = (completed.stderr or "").strip()

        if len(output) > self.MAX_OUTPUT_CHARS:
            output = output[:self.MAX_OUTPUT_CHARS] + "\n...[output truncated]"
        if len(error) > self.MAX_OUTPUT_CHARS:
            error = error[:self.MAX_OUTPUT_CHARS] + "\n...[output truncated]"

        if completed.returncode == 0:
            return ToolResult.ok(
                output=output,
                metadata={"returncode": completed.returncode},
            ).to_dict()

        return ToolResult.fail(
            error or "Execution failed",
            output=output,
            metadata={"returncode": completed.returncode},
        ).to_dict()
