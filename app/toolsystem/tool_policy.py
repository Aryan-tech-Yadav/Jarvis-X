"""Tool execution policy and workspace boundary sandboxing."""

from __future__ import annotations

import os
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
        cmd_clean = command.strip().lower()
        for forbidden in self.FORBIDDEN_COMMANDS:
            if forbidden in cmd_clean:
                return False
        return True
