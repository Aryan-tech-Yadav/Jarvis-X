"""Bounded command execution for project tools."""

import math
import os
import subprocess
import sys

from config import TIMEOUT
from app.tools.tool_result import ToolResult
from app.tools.process_utils import run_bounded


class CommandRunner:
    MAX_OUTPUT_CHARS = 20000
    MAX_TIMEOUT = 300

    def __init__(self, timeout=TIMEOUT):
        try:
            value = float(timeout)
            if not math.isfinite(value) or not 1 <= value <= self.MAX_TIMEOUT:
                raise ValueError
        except (TypeError, ValueError, OverflowError):
            raise ValueError(
                f"timeout must be between 1 and {self.MAX_TIMEOUT} seconds"
            )
        self.timeout = value

    def run_python(self, base_path, file_name="main.py"):
        return self.run([sys.executable, file_name], base_path)

    def run_pip(self, base_path):
        return self.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            base_path,
        )

    def run_pytest(self, base_path):
        return self.run([sys.executable, "-m", "pytest"], base_path)

    def run(self, command, base_path):
        if not base_path or not os.path.isdir(base_path):
            return ToolResult(False, error="Invalid project path")

        if (
            not isinstance(command, (list, tuple))
            or not command
            or not all(isinstance(arg, str) and arg for arg in command)
        ):
            return ToolResult(
                False,
                error="Command must be a non-empty list of non-empty strings",
            )

        project_path = os.path.realpath(base_path)

        try:
            result = run_bounded(
                list(command),
                cwd=project_path,
                shell=False,
                text=True,
                timeout=self.timeout,
                max_output_chars=self.MAX_OUTPUT_CHARS,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                False,
                error=f"Command timed out after {self.timeout:g} seconds",
            )
        except (OSError, ValueError, TypeError, subprocess.SubprocessError) as exc:
            return ToolResult(False, error=str(exc))

        return ToolResult(
            success=result.returncode == 0,
            output=(result.stdout or "").strip(),
            error=(result.stderr or "").strip() or (
                None if result.returncode == 0
                else f"Command exited with code {result.returncode}"
            ),
            metadata={"returncode": result.returncode},
        )
