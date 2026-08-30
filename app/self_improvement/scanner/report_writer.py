"""Report writer for project scanner.

Generates:
  - JSON reports for machine consumption
  - Markdown reports for human reading
  - Mermaid dependency graphs
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class ProjectReport:
    """Complete project scan report."""

    project_path: str
    version: str = "1.0"
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    summary: Dict[str, Any] = field(default_factory=dict)
    files: List[Dict[str, Any]] = field(default_factory=list)
    dependencies: Dict[str, Any] = field(default_factory=dict)
    issues: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "project_path": self.project_path,
            "version": self.version,
            "generated_at": self.generated_at,
            "summary": dict(self.summary),
            "files": list(self.files),
            "dependencies": dict(self.dependencies),
            "issues": list(self.issues),
            "metadata": dict(self.metadata),
        }


class ReportWriter:
    """Write project scan reports in multiple formats."""

    def __init__(self, reports_dir: str = "reports"):
        self.reports_dir = reports_dir
        os.makedirs(reports_dir, exist_ok=True)

    def write_json(self, report: ProjectReport, filename: str | None = None) -> str:
        """Write JSON report.

        Args:
            report: ProjectReport to write.
            filename: Optional filename override.

        Returns:
            Path to written file.
        """
        filename = filename or f"{self._safe_name(report.project_path)}_report.json"
        path = os.path.join(self.reports_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, indent=2, default=str)
        return path

    def write_markdown(self, report: ProjectReport, filename: str | None = None) -> str:
        """Write Markdown report.

        Args:
            report: ProjectReport to write.
            filename: Optional filename override.

        Returns:
            Path to written file.
        """
        filename = filename or f"{self._safe_name(report.project_path)}_report.md"
        path = os.path.join(self.reports_dir, filename)
        content = self._build_markdown(report)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def write_mermaid(self, report: ProjectReport, filename: str | None = None) -> str:
        """Write Mermaid dependency graph.

        Args:
            report: ProjectReport to write.
            filename: Optional filename override.

        Returns:
            Path to written file.
        """
        filename = filename or f"{self._safe_name(report.project_path)}_graph.mmd"
        path = os.path.join(self.reports_dir, filename)
        content = self._build_mermaid(report)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def write_all(self, report: ProjectReport) -> Dict[str, str]:
        """Write all report formats.

        Args:
            report: ProjectReport to write.

        Returns:
            Dict of format -> file path.
        """
        return {
            "json": self.write_json(report),
            "markdown": self.write_markdown(report),
            "mermaid": self.write_mermaid(report),
        }

    def _build_markdown(self, report: ProjectReport) -> str:
        """Build markdown report content."""
        lines = [
            f"# Project Scan Report: {report.project_path}",
            "",
            f"**Version:** {report.version}",
            f"**Generated:** {report.generated_at}",
            "",
            "## Summary",
            "",
        ]
        for key, value in report.summary.items():
            lines.append(f"- **{key}:** {value}")

        lines.extend([
            "",
            "## Files",
            "",
            "| File | LOC | Classes | Functions | Complexity |",
            "|------|-----|---------|-----------|------------|",
        ])
        for file_data in sorted(report.files, key=lambda x: x.get("loc", 0), reverse=True)[:20]:
            name = file_data.get("path", "")
            loc = file_data.get("loc", 0)
            classes = file_data.get("classes", 0)
            functions = file_data.get("functions", 0)
            complexity = file_data.get("complexity", 0)
            lines.append(f"| {name} | {loc} | {classes} | {functions} | {complexity} |")

        if report.dependencies.get("cycles"):
            lines.extend([
                "",
                "## Circular Dependencies",
                "",
            ])
            for cycle in report.dependencies["cycles"]:
                lines.append(f"- {' -> '.join(cycle)}")

        if report.issues:
            lines.extend([
                "",
                "## Issues",
                "",
            ])
            for issue in report.issues[:20]:
                lines.append(f"- {issue}")

        lines.extend([
            "",
            "---",
            f"*Generated by Jarvis-X Project Scanner v{report.version}*",
        ])
        return "\n".join(lines)

    def _build_mermaid(self, report: ProjectReport) -> str:
        """Build Mermaid dependency graph."""
        lines = ["graph TD"]
        edges = report.dependencies.get("edges", [])
        for edge in edges[:50]:  # Limit for readability
            source = edge.get("source", "").replace("/", "_").replace(".", "_")
            target = edge.get("target", "").replace("/", "_").replace(".", "_")
            if source and target:
                lines.append(f"  {source} --> {target}")
        return "\n".join(lines)

    @staticmethod
    def _safe_name(path: str) -> str:
        """Convert path to safe filename."""
        return path.replace("/", "_").replace("\\", "_").replace(":", "_").replace(" ", "_")
