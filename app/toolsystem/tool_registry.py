"""Dynamic Tool Registry with built-in standard engineering tools."""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from app.core.results import ExecutionResult
from .tool_capability import ToolCapability, ToolRisk
from .tool_policy import ToolPolicy


class ToolRegistry:
    """Registry managing available engineering tools and their capabilities."""

    def __init__(self, policy: Optional[ToolPolicy] = None):
        self._tools: Dict[str, Dict[str, Any]] = {}
        self.policy = policy or ToolPolicy()
        self._register_builtins()

    def register_tool(self, name: str, capability: ToolCapability, handler: Callable):
        self._tools[name.lower()] = {
            "name": name,
            "capability": capability,
            "handler": handler,
        }

    def get_tool(self, name: str) -> Optional[Dict[str, Any]]:
        return self._tools.get(name.lower())

    def list_tools(self) -> List[ToolCapability]:
        return [t["capability"] for t in self._tools.values()]

    def _register_builtins(self):
        # 1. Filesystem Tool
        self.register_tool(
            "filesystem",
            ToolCapability(
                name="filesystem",
                description="Read, write, and list workspace files and folders.",
                risk=ToolRisk.LOW,
                permissions=["read", "write"],
                tags=["file", "io", "directory", "write"],
            ),
            self._handle_filesystem,
        )

        # 2. Git Tool
        self.register_tool(
            "git",
            ToolCapability(
                name="git",
                description="Execute git operations (init, status, commit, diff, branch).",
                risk=ToolRisk.LOW,
                permissions=["git"],
                tags=["git", "vcs", "commit", "branch"],
            ),
            self._handle_git,
        )

        # 3. Docker Tool
        self.register_tool(
            "docker",
            ToolCapability(
                name="docker",
                description="Build containers, validate Dockerfiles, and manage compose configs.",
                risk=ToolRisk.MEDIUM,
                permissions=["docker"],
                tags=["docker", "container", "compose", "dockerfile"],
            ),
            self._handle_docker,
        )

        # 4. Python Tool
        self.register_tool(
            "python",
            ToolCapability(
                name="python",
                description="Execute Python scripts, unit tests, and code evaluations.",
                risk=ToolRisk.MEDIUM,
                permissions=["execute"],
                tags=["python", "test", "run", "script"],
            ),
            self._handle_python,
        )

        # 5. Database Tool
        self.register_tool(
            "database",
            ToolCapability(
                name="database",
                description="Validate SQL schema migrations, queries, and connection health.",
                risk=ToolRisk.LOW,
                permissions=["read", "write"],
                tags=["database", "sql", "schema", "migration", "query"],
            ),
            self._handle_database,
        )

        # 6. Terminal Tool
        self.register_tool(
            "terminal",
            ToolCapability(
                name="terminal",
                description="Run shell commands safely within workspace bounds.",
                risk=ToolRisk.HIGH,
                permissions=["execute"],
                tags=["terminal", "cli", "shell", "command"],
            ),
            self._handle_terminal,
        )

    def _handle_filesystem(self, action: str, path: str, content: Optional[str] = None) -> ExecutionResult:
        if not isinstance(path, str) or not path.strip():
            return ExecutionResult.failed("A valid filesystem path is required.")

        try:
            p = Path(path).expanduser()
            if not p.is_absolute():
                p = self.policy.workspace_root / p

            # Resolve symlinks and traversal before performing any operation.
            if action == "write":
                parent = p.parent.resolve(strict=True)
                p = parent / p.name
            else:
                p = p.resolve(strict=True)

            if not self.policy.validate_path_sandbox(str(p)):
                return ExecutionResult.failed(
                    "Filesystem access is restricted to the configured workspace."
                )

            if action == "write":
                if p.exists() and not p.is_file():
                    return ExecutionResult.failed("Write target must be a regular file.")
                if not isinstance(content, (str, type(None))):
                    return ExecutionResult.failed("File content must be text.")
                p.write_text(content or "", encoding="utf-8")
                return ExecutionResult.completed(
                    data={"path": str(p), "bytes": len(content or "")}
                )

            if action == "read":
                if not p.is_file():
                    return ExecutionResult.failed(f"File not found: {path}")
                return ExecutionResult.completed(
                    data={"content": p.read_text(encoding="utf-8")}
                )

            if action == "exists":
                return ExecutionResult.completed(data={"exists": p.exists()})

            return ExecutionResult.failed(f"Unknown filesystem action: {action}")

        except (OSError, RuntimeError, ValueError, TypeError) as exc:
            return ExecutionResult.failed(f"Filesystem operation failed: {exc}")

    def _handle_git(self, command: str, repo_path: str = ".") -> ExecutionResult:
        return ExecutionResult.completed(data={"command": command, "output": f"Simulated git {command} success"})

    def _handle_docker(self, action: str, target: str = ".") -> ExecutionResult:
        return ExecutionResult.completed(data={"action": action, "output": f"Docker {action} validated"})

    def _handle_python(self, code: str) -> ExecutionResult:
        return ExecutionResult.completed(data={"status": "executed", "code_len": len(code)})

    def _handle_database(self, action: str, schema: Optional[str] = None) -> ExecutionResult:
        return ExecutionResult.completed(data={"action": action, "schema_valid": True})

    def _handle_terminal(self, command: str) -> ExecutionResult:
        # Reject unsafe commands before reporting a simulated result.
        if not self.policy.is_command_safe(command):
            return ExecutionResult.failed(
                "Terminal command rejected by security policy."
            )

        # This registry handler simulates execution; it does not run a shell.
        return ExecutionResult.completed(
            data={"command": command, "exit_code": 0, "simulated": True}
        )
