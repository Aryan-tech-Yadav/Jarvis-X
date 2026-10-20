"""Permission manager for tool execution.

Controls which tools require user approval and enforces safety rules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PermissionRule:
    """Permission rule for a tool or action."""

    tool_name: str
    action: str = ""
    required_permission: str = ""
    auto_approve: bool = False
    description: str = ""


@dataclass
class PermissionResult:
    """Result of a permission check."""

    allowed: bool
    reason: str = ""
    requires_approval: bool = False
    rule: Optional[PermissionRule] = None


class PermissionManager:
    """Manage tool permissions and approval workflows."""

    DANGEROUS_PERMISSIONS = {
        "filesystem.delete",
        "filesystem.format",
        "system.shutdown",
        "system.reboot",
        "network.destructive",
        "database.drop",
        "docker.privileged",
        "git.force_push",
        "terminal.sudo",
        "vscode.remote_exec",
    }

    def __init__(self, auto_approve: bool = False):
        self.auto_approve = auto_approve
        self._rules: List[PermissionRule] = []
        self._approval_callbacks: List[Any] = []

    def add_rule(self, rule: PermissionRule):
        """Add a permission rule."""
        self._rules.append(rule)

    def add_approval_callback(self, callback):
        """Register a callback for approval requests."""
        self._approval_callbacks.append(callback)

    def check(self, tool_name: str, action: str, permissions: List[str]) -> PermissionResult:
        """Check if a tool action is allowed."""
        required = set(permissions or [])
        dangerous = required & self.DANGEROUS_PERMISSIONS
        if not dangerous:
            return PermissionResult(allowed=True)

        matching_rule = next((r for r in self._rules
                              if r.tool_name == tool_name and (r.action == action or not r.action)
                              and r.required_permission in dangerous), None)

        if matching_rule and matching_rule.auto_approve:
            return PermissionResult(allowed=True, reason="Auto-approved by rule", rule=matching_rule)

        # Global auto-approval must never bypass dangerous permissions.
        # Dangerous operations require an explicit matching rule or approval callback.

        for callback in self._approval_callbacks:
            try:
                approved = callback(tool_name, action, list(dangerous))
                if approved:
                    return PermissionResult(allowed=True, reason="User approved", requires_approval=True)
            except Exception:
                continue

        return PermissionResult(
            allowed=False,
            reason=f"Permission denied: {', '.join(sorted(dangerous))}",
            requires_approval=True,
            rule=matching_rule,
        )

    def rules(self) -> List[Dict[str, Any]]:
        return [r.__dict__ for r in self._rules]
