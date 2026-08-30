"""Engineering report generator.

Generates Markdown and PDF reports for completed engineering runs.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class EngineeringReport:
    """Structured engineering report data."""

    project_name: str = ""
    goal: str = ""
    status: str = "pending"
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    duration_seconds: float = 0.0
    requirements: Dict[str, Any] = field(default_factory=dict)
    architecture: Dict[str, Any] = field(default_factory=dict)
    files_generated: List[str] = field(default_factory=list)
    tests: Dict[str, Any] = field(default_factory=dict)
    coverage: Dict[str, Any] = field(default_factory=dict)
    performance: Dict[str, Any] = field(default_factory=dict)
    security: Dict[str, Any] = field(default_factory=dict)
    benchmark: Dict[str, Any] = field(default_factory=dict)
    known_issues: List[str] = field(default_factory=list)
    future_improvements: List[str] = field(default_factory=list)
    llm_usage: Dict[str, Any] = field(default_factory=dict)
    overall_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "goal": self.goal,
            "status": self.status,
            "generated_at": self.generated_at,
            "duration_seconds": round(self.duration_seconds, 3),
            "requirements": dict(self.requirements),
            "architecture": dict(self.architecture),
            "files_generated": list(self.files_generated),
            "tests": dict(self.tests),
            "coverage": dict(self.coverage),
            "performance": dict(self.performance),
            "security": dict(self.security),
            "benchmark": dict(self.benchmark),
            "known_issues": list(self.known_issues),
            "future_improvements": list(self.future_improvements),
            "llm_usage": dict(self.llm_usage),
            "overall_score": round(self.overall_score, 2),
            "metadata": dict(self.metadata),
        }


class ReportGenerator:
    """Generate Markdown and PDF engineering reports."""

    def __init__(self, reports_dir: str = "reports"):
        self.reports_dir = reports_dir
        os.makedirs(reports_dir, exist_ok=True)

    def generate(self, report: EngineeringReport) -> Dict[str, str]:
        """Generate Markdown and optional PDF reports."""
        md_path = os.path.join(self.reports_dir, f"{report.project_name or 'project'}_report.md")
        pdf_path = os.path.join(self.reports_dir, f"{report.project_name or 'project'}_report.pdf")
        
        md_content = self._build_markdown(report)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        
        pdf_content = self._build_pdf_text(report)
        with open(pdf_path, "w", encoding="utf-8") as f:
            f.write(pdf_content)
        
        return {"markdown": md_path, "pdf": pdf_path}

    def _build_markdown(self, report: EngineeringReport) -> str:
        lines = [
            f"# Engineering Report: {report.project_name or 'Project'}",
            "",
            "## Summary",
            f"- **Goal**: {report.goal}",
            f"- **Status**: {report.status}",
            f"- **Duration**: {report.duration_seconds:.2f}s",
            f"- **Generated**: {report.generated_at}",
            f"- **Overall Score**: {report.overall_score}%",
            "",
            "## Requirements",
            json.dumps(report.requirements, indent=2) if report.requirements else "N/A",
            "",
            "## Architecture",
            json.dumps(report.architecture, indent=2) if report.architecture else "N/A",
            "",
            "## Files Generated",
        ]
        if report.files_generated:
            for file_path in report.files_generated:
                lines.append(f"- {file_path}")
        else:
            lines.append("N/A")
        
        lines.extend([
            "",
            "## Tests",
            json.dumps(report.tests, indent=2) if report.tests else "N/A",
            "",
            "## Coverage",
            json.dumps(report.coverage, indent=2) if report.coverage else "N/A",
            "",
            "## Performance",
            json.dumps(report.performance, indent=2) if report.performance else "N/A",
            "",
            "## Security",
            json.dumps(report.security, indent=2) if report.security else "N/A",
            "",
            "## Benchmark",
            json.dumps(report.benchmark, indent=2) if report.benchmark else "N/A",
            "",
            "## Known Issues",
        ])
        if report.known_issues:
            for issue in report.known_issues:
                lines.append(f"- {issue}")
        else:
            lines.append("None")
        
        lines.extend([
            "",
            "## Future Improvements",
        ])
        if report.future_improvements:
            for improvement in report.future_improvements:
                lines.append(f"- {improvement}")
        else:
            lines.append("None")
        
        lines.extend([
            "",
            "## LLM Usage",
            json.dumps(report.llm_usage, indent=2) if report.llm_usage else "N/A",
            "",
            "---",
            f"*Report generated at {report.generated_at}*",
        ])
        return "\n".join(lines)

    def _build_pdf_text(self, report: EngineeringReport) -> str:
        """Plain text fallback for PDF-style output."""
        lines = [
            "=" * 60,
            f"ENGINEERING REPORT: {report.project_name or 'Project'}",
            "=" * 60,
            f"Goal: {report.goal}",
            f"Status: {report.status}",
            f"Duration: {report.duration_seconds:.2f}s",
            f"Score: {report.overall_score}%",
            "",
            "-" * 60,
            "REQUIREMENTS",
            "-" * 60,
            json.dumps(report.requirements, indent=2) if report.requirements else "N/A",
            "",
            "-" * 60,
            "ARCHITECTURE",
            "-" * 60,
            json.dumps(report.architecture, indent=2) if report.architecture else "N/A",
            "",
            "-" * 60,
            "FILES GENERATED",
            "-" * 60,
            "\n".join(f"- {f}" for f in report.files_generated) or "N/A",
            "",
            "-" * 60,
            "BENCHMARK",
            "-" * 60,
            json.dumps(report.benchmark, indent=2) if report.benchmark else "N/A",
            "",
            "-" * 60,
            "KNOWN ISSUES",
            "-" * 60,
            "\n".join(f"- {i}" for i in report.known_issues) or "None",
            "",
            "-" * 60,
            "FUTURE IMPROVEMENTS",
            "-" * 60,
            "\n".join(f"- {i}" for i in report.future_improvements) or "None",
            "",
            "=" * 60,
            f"Generated: {report.generated_at}",
            "=" * 60,
        ]
        return "\n".join(lines)
