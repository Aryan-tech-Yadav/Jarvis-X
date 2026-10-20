"""Tool execution policy and workspace boundary sandboxing."""

from __future__ import annotations

import os
import shlex
from pathlib import Path
from typing import Any, Dict, List, Optional

from .tool_capability import ToolCapability, ToolRisk


class ToolPolicy:
    """Enforces permissions, dangerous command blocks, and workspace path sandboxing."""

    FORBIDDEN_COMMANDS = {
        "rm -rf /",
        "rm -rf ~",
        "mkfs",
        ":(){ :|:& };:",
        "dd if=/dev/zero",
        "format c:",
    }

    # Keep this allowlist conservative. TerminalTool has its own execution
    # restrictions; this policy also protects ToolRegistry's terminal route.
    ALLOWED_COMMANDS = {"echo", "pwd", "ls", "whoami", "pytest", "python"}

    def __init__(self, workspace_root: Optional[str] = None, allowed_permissions: Optional[List[str]] = None):
        self.workspace_root = Path(workspace_root).resolve() if workspace_root else Path.cwd()
        self.allowed_permissions = set(allowed_permissions or ["read", "write", "execute", "network", "git", "docker"])

    def check_permissions(self, capability: ToolCapability) -> bool:
        for perm in capability.permissions:
            if perm not in self.allowed_permissions:
                return False
        return True

    def validate_path_sandbox(self, target_path: str) -> bool:
        try:
            resolved = Path(target_path).resolve()
            return self.workspace_root in resolved.parents or resolved == self.workspace_root
        except Exception:
            return False

    def is_command_safe(self, command: str) -> bool:
        """Accept only simple commands whose executable is explicitly allowed."""
        if not isinstance(command, str) or not command.strip():
            return False

        cmd_clean = command.strip().lower()
        if any(pattern in cmd_clean for pattern in self.FORBIDDEN_COMMANDS):
            return False

        try:
            lexer = shlex.shlex(
                command,
                posix=True,
                punctuation_chars=";&|<>",
            )
            lexer.whitespace_split = True
            tokens = list(lexer)
        except (ValueError, TypeError):
            return False

        if not tokens:
            return False

        shell_punctuation = set(";&|<>")
        if any(
            token and all(char in shell_punctuation for char in token)
            for token in tokens
        ):
            return False

        executable = tokens[0].lower()
        # Do not allow absolute or relative executable paths.
        if "/" in tokens[0] or "\\\\" in tokens[0]:
            return False
        if executable not in self.ALLOWED_COMMANDS:
            return False

        # Python is limited to a harmless version query.
        if executable == "python":
            return tokens == ["python", "--version"]

        return True
