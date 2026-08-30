"""Benchmark Engine for Jarvis-X.

Automatically calculates project scores across multiple dimensions:
  - Planning
  - Architecture
  - Testing
  - Security
  - Performance
  - Repair efficiency
  - Documentation
  - Deployment readiness

Outputs overall score and breakdown.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class BenchmarkScore:
    """Benchmark score for a single dimension."""

    dimension: str
    score: float = 0.0
    max_score: float = 100.0
    weight: float = 1.0
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "dimension": self.dimension,
            "score": self.score,
            "max_score": self.max_score,
            "weight": self.weight,
            "details": dict(self.details),
        }


@dataclass
class BenchmarkReport:
    """Complete benchmark report for a project."""

    project_name: str = ""
    overall_score: float = 0.0
    dimensions: List[BenchmarkScore] = field(default_factory=list)
    grade: str = "F"
    created_at: str = ""

    def to_dict(self) -> dict:
        return {
            "project_name": self.project_name,
            "overall_score": self.overall_score,
            "dimensions": [d.to_dict() for d in self.dimensions],
            "grade": self.grade,
            "created_at": self.created_at,
        }


class BenchmarkEngine:
    """Calculate project benchmarks across multiple dimensions."""

    DEFAULT_DIMENSIONS = [
        ("planning", 1.0),
        ("architecture", 1.2),
        ("testing", 1.1),
        ("security", 1.0),
        ("performance", 0.9),
        ("repair_efficiency", 0.8),
        ("documentation", 0.7),
        ("deployment", 0.8),
    ]

    def __init__(self, benchmarks_path: str = "data/benchmarks.json"):
        self.benchmarks_path = benchmarks_path
        self._history: List[BenchmarkReport] = []
        os.makedirs(os.path.dirname(benchmarks_path) or ".", exist_ok=True)
        self._load()

    def _load(self):
        if not os.path.exists(self.benchmarks_path):
            return
        try:
            with open(self.benchmarks_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            if isinstance(raw, list):
                self._history = [BenchmarkReport(
                    project_name=r.get("project_name", ""),
                    overall_score=r.get("overall_score", 0.0),
                    dimensions=[BenchmarkScore(**d) for d in r.get("dimensions", [])],
                    grade=r.get("grade", "F"),
                    created_at=r.get("created_at", ""),
                ) for r in raw if isinstance(r, dict)]
        except (OSError, json.JSONDecodeError, TypeError):
            pass

    def _save(self):
        try:
            with open(self.benchmarks_path, "w", encoding="utf-8") as f:
                json.dump([r.to_dict() for r in self._history], f, indent=2, default=str)
        except OSError:
            pass

    def evaluate(self, project_name: str, metrics: Dict[str, Any]) -> BenchmarkReport:
        """Evaluate a project and generate a benchmark report."""
        dimensions = []
        total_weighted = 0.0
        total_weight = 0.0

        for dim_name, weight in self.DEFAULT_DIMENSIONS:
            score = self._score_dimension(dim_name, metrics)
            details = self._details_for_dimension(dim_name, metrics)
            dimensions.append(BenchmarkScore(
                dimension=dim_name,
                score=score,
                weight=weight,
                details=details,
            ))
            total_weighted += score * weight
            total_weight += weight

        overall = total_weighted / max(1.0, total_weight)
        grade = self._grade(overall)

        report = BenchmarkReport(
            project_name=project_name,
            overall_score=overall,
            dimensions=dimensions,
            grade=grade,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._history.append(report)
        self._save()
        return report

    def _score_dimension(self, dimension: str, metrics: Dict[str, Any]) -> float:
        """Score a single dimension based on metrics."""
        if dimension == "planning":
            return float(metrics.get("planning_score", 0.0))
        if dimension == "architecture":
            return float(metrics.get("architecture_score", metrics.get("quality_score", 0.0)))
        if dimension == "testing":
            return float(metrics.get("test_coverage", 0.0))
        if dimension == "security":
            return float(metrics.get("security_score", 0.0))
        if dimension == "performance":
            return float(metrics.get("performance_score", 0.0))
        if dimension == "repair_efficiency":
            repair_count = int(metrics.get("repair_count", 0))
            max_repairs = metrics.get("max_repairs", 5)
            return max(0.0, 100.0 - (repair_count / max(1, max_repairs)) * 100.0)
        if dimension == "documentation":
            return 100.0 if metrics.get("documentation_complete", False) else 50.0
        if dimension == "deployment":
            return 100.0 if metrics.get("deployment_ready", False) else 30.0
        return 50.0

    def _details_for_dimension(self, dimension: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Get details for a dimension score."""
        details = {}
        if dimension == "testing":
            details["coverage"] = metrics.get("test_coverage", 0.0)
            details["tests_count"] = metrics.get("tests_count", 0)
        if dimension == "repair_efficiency":
            details["repair_count"] = metrics.get("repair_count", 0)
        if dimension == "planning":
            details["planning_score"] = metrics.get("planning_score", 0.0)
        return details

    def _grade(self, score: float) -> str:
        if score >= 90:
            return "A"
        if score >= 80:
            return "B"
        if score >= 70:
            return "C"
        if score >= 60:
            return "D"
        return "F"

    def history(self) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self._history]

    def compare(self, project_name: str) -> Optional[Dict[str, Any]]:
        """Compare latest project with historical average."""
        if not self._history:
            return None
        latest = self._history[-1]
        avg = sum(r.overall_score for r in self._history[:-1]) / max(1, len(self._history) - 1)
        return {
            "project_name": project_name,
            "latest_score": latest.overall_score,
            "historical_avg": avg,
            "delta": latest.overall_score - avg,
            "grade": latest.grade,
        }
