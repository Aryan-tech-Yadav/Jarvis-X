"""Evolution Scorecard, Weekly Self-Review Generator, and Evolution Dashboard."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class EvolutionScoreCalculator:
    """Calculates weighted evolution scores across Planning, Execution, QA, Repair, Performance, and Learning."""

    WEIGHTS = {
        "planning": 0.20,
        "execution": 0.20,
        "qa": 0.15,
        "repair": 0.15,
        "performance": 0.15,
        "learning": 0.15,
    }

    @classmethod
    def compute_score(
        cls,
        planning_score: float = 96.0,
        execution_score: float = 94.0,
        qa_score: float = 95.0,
        repair_score: float = 92.0,
        performance_score: float = 90.0,
        learning_score: float = 97.0,
    ) -> Dict[str, Any]:
        breakdown = {
            "planning": round(float(planning_score), 2),
            "execution": round(float(execution_score), 2),
            "qa": round(float(qa_score), 2),
            "repair": round(float(repair_score), 2),
            "performance": round(float(performance_score), 2),
            "learning": round(float(learning_score), 2),
        }

        overall = sum(breakdown[k] * cls.WEIGHTS[k] for k in cls.WEIGHTS)

        return {
            "overall_evolution_score": round(overall, 2),
            "breakdown": breakdown,
            "grade": "A+" if overall >= 95.0 else ("A" if overall >= 90.0 else ("B" if overall >= 80.0 else "C")),
            "weights": cls.WEIGHTS,
        }


class WeeklySelfReview:
    """Generates automated weekly self-review reports and evolution dashboard widgets."""

    def __init__(
        self,
        total_projects: int = 18,
        success_count: int = 16,
        failure_count: int = 2,
        most_common_issues: Optional[List[str]] = None,
        recommended_focus: str = "Improve Config Loader and Parallel Execution",
        evolution_score: float = 94.8,
        knowledge_growth_entries: int = 42,
        benchmark_trend: str = "Positive (+3.2%)",
    ):
        self.total_projects = total_projects
        self.success_count = success_count
        self.failure_count = failure_count
        self.most_common_issues = most_common_issues or ["Configuration", "Circular Import"]
        self.recommended_focus = recommended_focus
        self.evolution_score = evolution_score
        self.knowledge_growth_entries = knowledge_growth_entries
        self.benchmark_trend = benchmark_trend
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "projects_summary": {
                "total": self.total_projects,
                "successful": self.success_count,
                "failed": self.failure_count,
                "success_rate_pct": round((self.success_count / max(1, self.total_projects)) * 100.0, 1),
            },
            "most_common_issues": self.most_common_issues,
            "recommended_focus": self.recommended_focus,
            "evolution_score": self.evolution_score,
            "knowledge_growth_entries": self.knowledge_growth_entries,
            "benchmark_trend": self.benchmark_trend,
        }

    def to_markdown(self) -> str:
        rate = (self.success_count / max(1, self.total_projects)) * 100.0 if self.total_projects > 0 else 100.0
        lines = [
            "# 📈 Jarvis-X Weekly Autonomous Self-Review",
            f"**Report Period:** `Last 7 Days` | **Generated:** `{self.timestamp}`",
            "",
            "## 📊 Executive Summary",
            f"- **Total Projects Processed:** `{self.total_projects}`",
            f"- **Successful Deliveries:** `{self.success_count}` ({rate:.1f}%)",
            f"- **Failures / Self-Healed:** `{self.failure_count}`",
            f"- **Evolution Score:** **`{self.evolution_score:.1f}%`**",
            f"- **Knowledge Growth:** `+{self.knowledge_growth_entries} new patterns & lessons`",
            "",
            "## 🔍 Recurring Failure Patterns",
        ]
        for issue in self.most_common_issues:
            lines.append(f"- ⚠️ `{issue}`")

        lines.extend([
            "",
            "## 💡 Recommended Focus & Strategy",
            f"> **{self.recommended_focus}**",
            "",
            "## 🧭 Evolution Dashboard Widgets",
            "```text",
            f"  Experience:         {self.total_projects:>4} projects recorded",
            f"  Success Rate:       {rate:>5.1f}%",
            f"  Knowledge Growth:   +{self.knowledge_growth_entries} entries",
            f"  Benchmark Trend:    {self.benchmark_trend}",
            f"  Evolution Score:    {self.evolution_score:.1f}%",
            "```",
        ])
        return "\n".join(lines)
