"""Quality scoring and coverage metrics.

Tracks quality metrics for project execution:
  - test coverage
  - test pass rate
  - code quality score
  - security score
  - architecture score
  - overall quality index

Example output:
  Quality Score      94/100
  Test Coverage      96%
  Tests Passed       142/145
  Security Score     95/100
  Architecture       97/100
  Performance        91/100
  Overall            95.8
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class QualityDimension:
    """Single quality dimension score."""

    name: str = ""
    score: float = 0.0
    max_score: float = 100.0
    weight: float = 1.0
    details: Dict[str, Any] = field(default_factory=dict)

    @property
    def normalized(self) -> float:
        """Get normalized score (0-100)."""
        if self.max_score == 0:
            return 0.0
        return (self.score / self.max_score) * 100.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "score": round(self.score, 2),
            "max_score": self.max_score,
            "weight": self.weight,
            "normalized": round(self.normalized, 2),
            "details": dict(self.details),
        }


@dataclass
class TestMetrics:
    """Test-related quality metrics."""

    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    coverage_percent: float = 0.0
    execution_time: float = 0.0

    @property
    def pass_rate(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return (self.passed / self.total_tests) * 100.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_tests": self.total_tests,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "coverage_percent": round(self.coverage_percent, 2),
            "pass_rate": round(self.pass_rate, 2),
            "execution_time": round(self.execution_time, 3),
        }


@dataclass
class QualityReport:
    """Complete quality report for a project execution."""

    project_name: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    dimensions: List[QualityDimension] = field(default_factory=list)
    test_metrics: TestMetrics = field(default_factory=TestMetrics)
    overall_score: float = 0.0
    grade: str = "F"
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "timestamp": self.timestamp,
            "dimensions": [d.to_dict() for d in self.dimensions],
            "test_metrics": self.test_metrics.to_dict(),
            "overall_score": round(self.overall_score, 2),
            "grade": self.grade,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "recommendations": list(self.recommendations),
        }


class QualityMetricsEngine:
    """Calculate and track quality metrics."""

    DEFAULT_WEIGHTS = {
        "code_quality": 0.20,
        "test_coverage": 0.20,
        "security": 0.15,
        "architecture": 0.15,
        "performance": 0.15,
        "documentation": 0.15,
    }

    def __init__(self, quality_path: str = os.path.join("data", "quality.json")):
        self.quality_path = quality_path
        self._reports: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        if os.path.isfile(self.quality_path):
            try:
                with open(self.quality_path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                if isinstance(raw, list):
                    self._reports = raw
            except (OSError, json.JSONDecodeError, TypeError):
                pass

    def _save(self):
        os.makedirs(os.path.dirname(self.quality_path), exist_ok=True)
        with open(self.quality_path, "w", encoding="utf-8") as f:
            json.dump(self._reports, f, indent=2, default=str)

    def calculate_quality(
        self,
        project_name: str = "",
        code_metrics: Optional[Dict[str, Any]] = None,
        test_results: Optional[Dict[str, Any]] = None,
        security_results: Optional[Dict[str, Any]] = None,
        performance_results: Optional[Dict[str, Any]] = None,
        architecture_score: Optional[float] = None,
        documentation_ratio: Optional[float] = None,
        custom_dimensions: Optional[Dict[str, float]] = None,
    ) -> QualityReport:
        """Calculate comprehensive quality metrics."""
        dimensions = []

        code_quality = self._calc_code_quality(code_metrics or {})
        dimensions.append(QualityDimension(
            name="code_quality",
            score=code_quality,
            weight=self.DEFAULT_WEIGHTS["code_quality"],
        ))

        test_coverage = self._calc_test_coverage(test_results or {})
        dimensions.append(QualityDimension(
            name="test_coverage",
            score=test_coverage,
            weight=self.DEFAULT_WEIGHTS["test_coverage"],
        ))

        security = self._calc_security_score(security_results or {})
        dimensions.append(QualityDimension(
            name="security",
            score=security,
            weight=self.DEFAULT_WEIGHTS["security"],
        ))

        arch = architecture_score if architecture_score is not None else 75.0
        dimensions.append(QualityDimension(
            name="architecture",
            score=arch,
            weight=self.DEFAULT_WEIGHTS["architecture"],
        ))

        perf = self._calc_performance_score(performance_results or {})
        dimensions.append(QualityDimension(
            name="performance",
            score=perf,
            weight=self.DEFAULT_WEIGHTS["performance"],
        ))

        doc = (documentation_ratio or 0.0) * 100
        dimensions.append(QualityDimension(
            name="documentation",
            score=doc,
            weight=self.DEFAULT_WEIGHTS["documentation"],
        ))

        if custom_dimensions:
            for name, score in custom_dimensions.items():
                dimensions.append(QualityDimension(name=name, score=score))

        overall = self._calc_overall(dimensions)
        grade = self._score_to_grade(overall)

        test_metrics = self._build_test_metrics(test_results or {})
        warnings, errors, recommendations = self._generate_feedback(dimensions, test_metrics)

        report = QualityReport(
            project_name=project_name,
            dimensions=dimensions,
            test_metrics=test_metrics,
            overall_score=overall,
            grade=grade,
            warnings=warnings,
            errors=errors,
            recommendations=recommendations,
        )

        self._reports.append(report.to_dict())
        self._save()

        return report

    def _calc_code_quality(self, code_metrics: Dict[str, Any]) -> float:
        """Calculate code quality score from code metrics."""
        score = 100.0

        avg_complexity = code_metrics.get("avg_complexity", 0)
        if avg_complexity > 10:
            score -= min(30, (avg_complexity - 10) * 3)
        elif avg_complexity > 7:
            score -= min(15, (avg_complexity - 7) * 5)

        duplication = code_metrics.get("duplication_estimate", 0)
        score -= duplication * 30

        avg_func_length = code_metrics.get("avg_function_length", 0)
        if avg_func_length > 50:
            score -= min(20, (avg_func_length - 50) * 0.5)

        doc_ratio = code_metrics.get("documentation_ratio", 0)
        if doc_ratio < 0.1:
            score -= 15
        elif doc_ratio < 0.2:
            score -= 5

        return max(0.0, min(100.0, score))

    def _calc_test_coverage(self, test_results: Dict[str, Any]) -> float:
        """Calculate test coverage score."""
        coverage = test_results.get("coverage_percent", 0)
        passed = test_results.get("passed", 0)
        total = test_results.get("total_tests", 0)

        if total == 0:
            return 0.0

        pass_rate = (passed / total) * 100
        return (coverage * 0.6) + (pass_rate * 0.4)

    def _calc_security_score(self, security_results: Dict[str, Any]) -> float:
        """Calculate security score."""
        score = 100.0
        vulnerabilities = security_results.get("vulnerabilities", 0)
        critical = security_results.get("critical", 0)
        warnings = security_results.get("warnings", 0)

        score -= critical * 20
        score -= vulnerabilities * 5
        score -= warnings * 1

        return max(0.0, min(100.0, score))

    def _calc_performance_score(self, performance_results: Dict[str, Any]) -> float:
        """Calculate performance score."""
        score = 100.0
        duration = performance_results.get("total_duration", 0)
        peak_memory = performance_results.get("peak_memory_mb", 0)

        if duration > 300:
            score -= min(30, (duration - 300) / 10)
        if peak_memory > 1024:
            score -= min(20, (peak_memory - 1024) / 100)

        return max(0.0, min(100.0, score))

    def _calc_overall(self, dimensions: List[QualityDimension]) -> float:
        """Calculate weighted overall score."""
        if not dimensions:
            return 0.0
        total_weight = sum(d.weight for d in dimensions)
        if total_weight == 0:
            return 0.0
        weighted_sum = sum(d.normalized * d.weight for d in dimensions)
        return weighted_sum / total_weight

    def _score_to_grade(self, score: float) -> str:
        """Convert numeric score to letter grade."""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        return "F"

    def _build_test_metrics(self, test_results: Dict[str, Any]) -> TestMetrics:
        """Build test metrics from results."""
        return TestMetrics(
            total_tests=test_results.get("total_tests", 0),
            passed=test_results.get("passed", 0),
            failed=test_results.get("failed", 0),
            skipped=test_results.get("skipped", 0),
            coverage_percent=test_results.get("coverage_percent", 0.0),
            execution_time=test_results.get("execution_time", 0.0),
        )

    def _generate_feedback(
        self,
        dimensions: List[QualityDimension],
        test_metrics: TestMetrics,
    ) -> tuple:
        """Generate warnings, errors, and recommendations."""
        warnings = []
        errors = []
        recommendations = []

        for dim in dimensions:
            if dim.normalized < 50:
                errors.append(f"{dim.name}: critical score {dim.normalized:.0f}/100")
            elif dim.normalized < 70:
                warnings.append(f"{dim.name}: below target ({dim.normalized:.0f}/100)")

        if test_metrics.coverage_percent < 80:
            recommendations.append("Increase test coverage to at least 80%")
        if test_metrics.pass_rate < 95:
            recommendations.append("Fix failing tests to improve pass rate")

        return warnings, errors, recommendations

    def get_latest_report(self) -> Optional[Dict[str, Any]]:
        """Get the latest quality report."""
        return self._reports[-1] if self._reports else None

    def format_report(self, report: Optional[QualityReport] = None) -> str:
        """Format a human-readable quality report."""
        if report is None:
            latest = self.get_latest_report()
            if not latest:
                return "No quality reports available."
            report = QualityReport(
                project_name=latest.get("project_name", ""),
                timestamp=latest.get("timestamp", ""),
                overall_score=latest.get("overall_score", 0),
                grade=latest.get("grade", "F"),
                warnings=latest.get("warnings", []),
                errors=latest.get("errors", []),
                recommendations=latest.get("recommendations", []),
            )
            for d in latest.get("dimensions", []):
                report.dimensions.append(QualityDimension(
                    name=d.get("name", ""),
                    score=d.get("score", 0),
                    max_score=d.get("max_score", 100),
                    weight=d.get("weight", 1),
                ))
            tm = latest.get("test_metrics", {})
            report.test_metrics = TestMetrics(
                total_tests=tm.get("total_tests", 0),
                passed=tm.get("passed", 0),
                failed=tm.get("failed", 0),
                skipped=tm.get("skipped", 0),
                coverage_percent=tm.get("coverage_percent", 0),
            )

        lines = [
            "Quality Report",
            "=" * 50,
            f"  Project:           {report.project_name}",
            f"  Overall Score:     {report.overall_score:.1f}/100",
            f"  Grade:             {report.grade}",
            "",
            "  Dimensions:",
        ]
        for dim in report.dimensions:
            lines.append(f"    {dim.name:<20} {dim.normalized:>6.1f}/100 (weight: {dim.weight:.0%})")

        lines.extend([
            "",
            "  Test Metrics:",
            f"    Total Tests:     {report.test_metrics.total_tests}",
            f"    Passed:          {report.test_metrics.passed}",
            f"    Failed:          {report.test_metrics.failed}",
            f"    Coverage:        {report.test_metrics.coverage_percent:.1f}%",
        ])

        if report.warnings:
            lines.extend(["", "  Warnings:"])
            for w in report.warnings:
                lines.append(f"    - {w}")
        if report.errors:
            lines.extend(["", "  Errors:"])
            for e in report.errors:
                lines.append(f"    - {e}")
        if report.recommendations:
            lines.extend(["", "  Recommendations:"])
            for r in report.recommendations:
                lines.append(f"    - {r}")

        return "\n".join(lines)
