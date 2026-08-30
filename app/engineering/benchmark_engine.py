"""Engineering benchmark engine.

Evaluates a generated project across multiple engineering dimensions and
produces a weighted overall score.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.core.logger import Logger
from app.core.results import ExecutionResult
from app.quality.qa_engine import QAEngine
from app.quality.quality_score import QualityScoreEngine


BENCHMARK_WEIGHTS = {
    "requirement": 10,
    "planning": 15,
    "architecture": 15,
    "backend": 20,
    "testing": 15,
    "security": 10,
    "performance": 5,
    "documentation": 10,
}


@dataclass
class BenchmarkReport:
    """Full benchmark report for a project."""

    project_name: str
    overall_score: float = 0.0
    grade: str = "F"
    passed: bool = False
    dimensions: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)
    gate_reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "overall_score": round(self.overall_score, 2),
            "grade": self.grade,
            "passed": self.passed,
            "dimensions": dict(self.dimensions),
            "suggestions": list(self.suggestions),
            "gate_reasons": list(self.gate_reasons),
        }


class BenchmarkEngine:
    """Evaluate a generated project against multi-dimensional quality gates."""

    def __init__(self, qa_engine=None, score_engine=None):
        self.qa_engine = qa_engine or QAEngine()
        self.score_engine = score_engine or QualityScoreEngine()

    def evaluate(self, project_path: str, requirements: Optional[Dict[str, Any]] = None) -> ExecutionResult:
        if not isinstance(project_path, str) or not project_path.strip():
            return ExecutionResult.failed("Project path cannot be empty")

        requirements = requirements or {}
        project_name = os.path.basename(project_path.strip().rstrip(os.sep))

        try:
            quality_score, static_result = self.qa_engine.evaluate_quality(project_path)
            report = self._build_report(project_name, requirements, quality_score, static_result)
            return ExecutionResult.completed(
                data=report.to_dict(),
                message="Benchmark evaluation complete",
                metrics={"overall_score": report.overall_score, "grade": report.grade, "passed": report.passed},
            )
        except Exception as exc:
            Logger.error(f"Benchmark evaluation failed: {exc}")
            return ExecutionResult.failed(str(exc))

    def _build_report(
        self,
        project_name: str,
        requirements: Dict[str, Any],
        quality_score,
        static_result,
    ) -> BenchmarkReport:
        dimensions: Dict[str, Dict[str, Any]] = {}
        total_weight = 0
        weighted_sum = 0.0

        dims = [
            ("requirement", self._score_requirement(requirements), BENCHMARK_WEIGHTS["requirement"]),
            ("planning", self._score_planning(requirements), BENCHMARK_WEIGHTS["planning"]),
            ("architecture", self._get_category_score(quality_score, "architecture"), BENCHMARK_WEIGHTS["architecture"]),
            ("backend", self._get_category_score(quality_score, "code_quality"), BENCHMARK_WEIGHTS["backend"]),
            ("testing", self._get_category_score(quality_score, "testing"), BENCHMARK_WEIGHTS["testing"]),
            ("security", self._get_category_score(quality_score, "security"), BENCHMARK_WEIGHTS["security"]),
            ("performance", self._get_category_score(quality_score, "performance"), BENCHMARK_WEIGHTS["performance"]),
            ("documentation", self._get_category_score(quality_score, "documentation"), BENCHMARK_WEIGHTS["documentation"]),
        ]

        for name, score, weight in dims:
            dimensions[name] = {"score": round(score, 2), "weight": weight}
            total_weight += weight
            weighted_sum += score * weight

        overall = round(weighted_sum / total_weight, 2) if total_weight else 0.0
        grade = self._grade(overall)
        passed = overall >= 85.0 and quality_score.passed_gate

        suggestions = list(quality_score.suggestions or [])
        gate_reasons = list(quality_score.gate_reasons or [])

        if not suggestions:
            suggestions.append("All benchmark criteria satisfied.")

        return BenchmarkReport(
            project_name=project_name,
            overall_score=overall,
            grade=grade,
            passed=passed,
            dimensions=dimensions,
            suggestions=suggestions,
            gate_reasons=gate_reasons,
        )

    @staticmethod
    def _get_category_score(quality_score, category_name: str) -> float:
        category = quality_score.category_scores.get(category_name)
        if category is None:
            return 0.0
        return getattr(category, "score", 0.0)

    @staticmethod
    def _score_requirement(requirements: Dict[str, Any]) -> float:
        modules = requirements.get("modules", [])
        if not modules:
            return 50.0
        return min(100.0, 60.0 + len(modules) * 8.0)

    @staticmethod
    def _score_planning(requirements: Dict[str, Any]) -> float:
        return 80.0 if requirements.get("backend") or requirements.get("frontend") else 40.0

    @staticmethod
    def _grade(score: float) -> str:
        if score >= 95.0:
            return "A+"
        if score >= 90.0:
            return "A"
        if score >= 80.0:
            return "B"
        if score >= 70.0:
            return "C"
        if score >= 60.0:
            return "D"
        return "F"
