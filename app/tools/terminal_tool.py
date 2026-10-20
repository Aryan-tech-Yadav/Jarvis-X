"""Terminal tool with safer command execution.

Actions: run, exec

String commands are restricted to a small allowlist and are never passed
through a shell. For complex commands, use a dedicated tool instead.
"""

from __future__ import annotations

import math
import os
import shlex
import shutil
import subprocess
import sys

from app.tools.base_tool import BaseTool, ToolMetadata, ToolResult
from app.tools.process_utils import run_bounded


class TerminalTool(BaseTool):
    metadata = ToolMetadata(
        name="terminal",
        description="Restricted terminal command execution",
        version="1.1.0",
        author="Jarvis",
        actions=["run", "exec"],
        permissions=["system.exec", "terminal"],
        tags=["terminal", "shell", "cli"],
    )

    DEFAULT_TIMEOUT = 30
    MAX_TIMEOUT = 300
    MAX_OUTPUT_CHARS = 20000

    # Explicitly supported commands. No shell operators, pipes or redirection.
    # Only basic informational commands are allowed here.
    # Use dedicated, permission-controlled tools for code execution,
    # package installation, Git operations, and project test execution.
    ALLOWED_COMMANDS = {"echo", "pwd", "ls", "whoami"}

    FORBIDDEN_PATTERNS = (
        "rm -rf /",
        "rm -rf /tmp",
        "del /f /s /q c:\\",
        "shutdown",
        "format",
        "sudo rm",
        "chmod -r 777 /",
        "rmdir /s /q c:\\",
    )

    def _truncate(self, value: str) -> str:
        value = value or ""
        if len(value) > self.MAX_OUTPUT_CHARS:
            return value[:self.MAX_OUTPUT_CHARS] + "\n...[output truncated]"
        return value

    def run(self, action: str = "", **kwargs) -> dict:
        if action not in self.metadata.actions:
            return ToolResult.fail(
                f"Unsupported action: {action}"
            ).to_dict()

        command = kwargs.get("command")
        if not command:
            return ToolResult.fail("Command is required").to_dict()

        if isinstance(command, str):
            command_text = command.strip()
            lowered = command_text.lower()

            for pattern in self.FORBIDDEN_PATTERNS:
                if pattern in lowered:
                    return ToolResult.fail(
                        f"Blocked dangerous command: {command}"
                    ).to_dict()

            # Reject shell syntax rather than trying to sanitize it.
            if any(token in command_text for token in (";", "&&", "||", "|", ">", "<", "`", "$(", "\n", "\r")):
                return ToolResult.fail(
                    "Blocked shell syntax. Run one allowed command at a time."
                ).to_dict()

            try:
                argv = shlex.split(command_text)
            except ValueError as exc:
                return ToolResult.fail(f"Invalid command: {exc}").to_dict()
        elif isinstance(command, (list, tuple)) and command:
            if not all(isinstance(part, str) for part in command):
                return ToolResult.fail("Command arguments must be strings").to_dict()
            argv = list(command)
            lowered = " ".join(argv).lower()
            for pattern in self.FORBIDDEN_PATTERNS:
                if pattern in lowered:
                    return ToolResult.fail(
                        f"Blocked dangerous command: {command}"
                    ).to_dict()
        else:
            return ToolResult.fail(
                "Command must be a string or a non-empty list of strings"
            ).to_dict()

        if os.path.basename(argv[0]) != argv[0]:
            return ToolResult.fail(
                "Executable paths are not allowed; use an allowlisted command name"
            ).to_dict()

        executable = os.path.basename(argv[0]).lower()

        # Permit only the harmless Python version query, not arbitrary code.
        safe_python_version = (
            executable in {"python", "python3"}
            and argv == [executable, "--version"]
        )

        # Fall back to the active interpreter if `python` is unavailable.
        if safe_python_version and shutil.which(executable) is None:
            argv = [sys.executable, "--version"]
            executable = os.path.basename(sys.executable).lower()

        if executable not in self.ALLOWED_COMMANDS and not safe_python_version:
            return ToolResult.fail(
                f"Blocked command: '{executable}' is not allowlisted"
            ).to_dict()

        cwd = kwargs.get("cwd") or kwargs.get("base_path") or os.getcwd()
        if not isinstance(cwd, str) or not os.path.isdir(cwd):
            return ToolResult.fail("Working directory must be an existing directory").to_dict()

        try:
            timeout = float(kwargs.get("timeout", self.DEFAULT_TIMEOUT))
            if not math.isfinite(timeout) or not 1 <= timeout <= self.MAX_TIMEOUT:
                return ToolResult.fail(
                    f"Timeout must be between 1 and {self.MAX_TIMEOUT} seconds"
                ).to_dict()

            completed = run_bounded(
                argv,
                max_output_chars=self.MAX_OUTPUT_CHARS,
                cwd=cwd,
                shell=False,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return ToolResult.fail(
                f"Command timed out after {timeout:g} seconds"
            ).to_dict()
        except (OSError, ValueError, TypeError) as exc:
            return ToolResult.fail(str(exc)).to_dict()

        output = self._truncate((completed.stdout or "").strip())
        error = self._truncate((completed.stderr or "").strip())
        metadata = {"returncode": completed.returncode}

        if completed.returncode == 0:
            return ToolResult.ok(output=output, metadata=metadata).to_dict()

        return ToolResult.fail(
            error or "Command failed",
            output=output,
            metadata=metadata,
        ).to_dict()
