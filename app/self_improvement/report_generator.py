"""Evolution report generator.

Generates detailed reports for self-evolution cycles.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class EvolutionReport:
    """Evolution report data."""

    evolution_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    baseline_score: float = 0.0
    final_score: float = 0.0
    score_improvement: float = 0.0
    improvements_applied: int = 0
    improvements_rejected: int = 0
    duration_seconds: float = 0.0
    applied_details: List[Dict[str, Any]] = field(default_factory=list)
    rejected_details: List[Dict[str, Any]] = field(default_factory=list)
    benchmark_comparison: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evolution_id": self.evolution_id,
            "timestamp": self.timestamp,
            "baseline_score": round(self.baseline_score, 2),
            "final_score": round(self.final_score, 2),
            "score_improvement": round(self.score_improvement, 2),
            "improvements_applied": self.improvements_applied,
            "improvements_rejected": self.improvements_rejected,
            "duration_seconds": round(self.duration_seconds, 3),
            "applied_details": list(self.applied_details),
            "rejected_details": list(self.rejected_details),
            "benchmark_comparison": dict(self.benchmark_comparison),
            "metadata": dict(self.metadata),
        }


class EvolutionReportGenerator:
    """Generate evolution reports."""

    def __init__(self, reports_dir: str = "reports"):
        self.reports_dir = reports_dir
        os.makedirs(reports_dir, exist_ok=True)

    def generate(self, result: Dict[str, Any]) -> Dict[str, str]:
        """Generate evolution report."""
        evolution_id = result.get("evolution_id", "unknown")
        md_path = os.path.join(self.reports_dir, f"evolution-{evolution_id}.md")
        
        content = self._build_markdown(result)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        return {"markdown": md_path}

    def _build_markdown(self, result: Dict[str, Any]) -> str:
        """Build markdown report."""
        baseline = result.get("baseline", {})
        final = result.get("final", {})
        comparison = result.get("comparison", {})
        applied = result.get("applied", [])
        rejected = result.get("rejected", [])
        
        lines = [
            f"# Evolution Report: {result.get('evolution_id', 'unknown')}",
            "",
            "## Summary",
            f"- **Baseline Score**: {baseline.get('quality_score', 0):.2f}",
            f"- **Final Score**: {final.get('quality_score', 0):.2f}",
            f"- **Improvement**: +{comparison.get('overall_change', 0):.2f}",
            f"- **Applied**: {len(applied)} improvements",
            f"- **Rejected**: {len(rejected)} improvements",
            f"- **Recommendation**: {comparison.get('recommendation', 'N/A')}",
            "",
        ]
        
        if applied:
            lines.extend([
                "## Applied Improvements",
                "",
            ])
            for item in applied:
                task = item.get("task", {})
                lines.append(f"- **{task.get('title', 'N/A')}** ({task.get('file', 'N/A')})")
            lines.append("")
        
        if rejected:
            lines.extend([
                "## Rejected Improvements",
                "",
            ])
            for item in rejected:
                task = item.get("task", {})
                lines.append(f"- **{task.get('title', 'N/A')}** - {item.get('reason', 'N/A')}")
            lines.append("")
        
        if comparison.get("improvements"):
            lines.extend([
                "## Benchmark Improvements",
                "",
            ])
            for imp in comparison["improvements"]:
                lines.append(f"- ✅ {imp}")
            lines.append("")
        
        if comparison.get("regressions"):
            lines.extend([
                "## Benchmark Regressions",
                "",
            ])
            for reg in comparison["regressions"]:
                lines.append(f"- ❌ {reg}")
            lines.append("")
        
        lines.extend([
            "---",
            f"*Report generated at {datetime.now(timezone.utc).isoformat()}*",
        ])
        
        return "\n".join(lines)
