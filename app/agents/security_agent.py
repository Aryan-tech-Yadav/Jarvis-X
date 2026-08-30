"""Security Agent - Reviews project for security vulnerabilities."""

from __future__ import annotations

import os
from typing import Any, Dict, List

from app.agents.base_agent import BaseAgent
from app.agents.project_context import ProjectContext
from app.core.logger import Logger


class SecurityAgent(BaseAgent):
    """Scans generated code for common security issues."""

    agent_id = "security"
    capabilities = ("security", "vulnerability", "audit", "scan")

    def run(self, context) -> Dict[str, Any]:
        if isinstance(context, dict):
            context = ProjectContext(**{k: v for k, v in context.items() if k in ProjectContext.__dataclass_fields__})
        
        project_path = context.project_path or ""
        if not project_path or not os.path.isdir(project_path):
            context.add_log("No project path available, skipping security scan")
            return {
                "success": True,
                "output": {"skipped": True, "reason": "No project path"},
                "context": context,
            }

        Logger.info("[SecurityAgent] Scanning for security issues")
        context.current_task = "security_scan"
        context.add_log("Starting security scan")

        issues = self._scan_project(project_path)
        context.add_completed_task("security_scan")
        context.set_metric("security_issues", len(issues))
        context.add_log(f"Security scan complete: {len(issues)} issues found")

        return {
            "success": True,
            "output": {"issues": issues, "count": len(issues)},
            "context": context,
        }

    def _scan_project(self, project_path: str) -> List[str]:
        """Basic security scan for common issues."""
        issues = []
        for root, _, files in os.walk(project_path):
            for filename in files:
                if not filename.endswith(".py"):
                    continue
                filepath = os.path.join(root, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                    if "eval(" in content:
                        issues.append(f"{filename}: unsafe eval() usage")
                    if "exec(" in content:
                        issues.append(f"{filename}: unsafe exec() usage")
                    if "password" in content.lower() and "=" in content:
                        issues.append(f"{filename}: possible hardcoded password")
                except (OSError, UnicodeDecodeError):
                    continue
        return issues
