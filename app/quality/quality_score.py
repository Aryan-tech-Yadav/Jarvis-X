"""Enterprise Quality Score Engine and Release Gate Evaluator."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .models.quality_result import (
    CategoryScore,
    IssueSeverity,
    PerformanceResult,
    QualityCategory,
    QualityIssue,
    QualityScore,
    SecurityResult,
    StaticAnalysisResult,
)
from .models.test_result import TestSuiteResult


class QualityScoreEngine:
    """Calculates weighted multi-dimensional quality scores and evaluates enterprise release gates."""

    DEFAULT_WEIGHTS = {
        QualityCategory.ARCHITECTURE: 0.20,
        QualityCategory.CODE_QUALITY: 0.20,
        QualityCategory.TESTING: 0.20,
        QualityCategory.SECURITY: 0.20,
        QualityCategory.PERFORMANCE: 0.10,
        QualityCategory.DOCUMENTATION: 0.10,
    }

    MIN_RELEASE_SCORE = 85.0
    MIN_COVERAGE_PCT = 85.0
    MIN_ARCH_SCORE = 85.0
    MIN_CODE_SCORE = 85.0

    def compute_overall_score(
        self,
        architecture_score: float,
        code_quality_score: float,
        test_suite_result: Optional[TestSuiteResult] = None,
        security_result: Optional[SecurityResult] = None,
        performance_result: Optional[PerformanceResult] = None,
        documentation_score: float = 95.0,
        custom_weights: Optional[Dict[QualityCategory, float]] = None,
        all_issues: Optional[List[QualityIssue]] = None,
    ) -> QualityScore:
        weights = custom_weights or self.DEFAULT_WEIGHTS

        # 1. Testing Score calculation
        if test_suite_result is not None:
            pass_rate = (test_suite_result.passed / max(1, test_suite_result.total_tests)) * 100.0 if test_suite_result.total_tests > 0 else 0.0
            cov_rate = test_suite_result.coverage.coverage_percentage
            test_score = (pass_rate * 0.5) + (cov_rate * 0.5)
        else:
            test_score = 90.0

        # 2. Security Score
        sec_score = security_result.security_score if security_result is not None else 100.0

        # 3. Performance Score
        perf_score = performance_result.performance_score if performance_result is not None else 100.0

        category_scores: Dict[str, CategoryScore] = {
            "architecture": CategoryScore(
                category=QualityCategory.ARCHITECTURE,
                score=round(max(0.0, min(100.0, architecture_score)), 2),
                weight=weights[QualityCategory.ARCHITECTURE],
            ),
            "code_quality": CategoryScore(
                category=QualityCategory.CODE_QUALITY,
                score=round(max(0.0, min(100.0, code_quality_score)), 2),
                weight=weights[QualityCategory.CODE_QUALITY],
            ),
            "testing": CategoryScore(
                category=QualityCategory.TESTING,
                score=round(max(0.0, min(100.0, test_score)), 2),
                weight=weights[QualityCategory.TESTING],
                metrics={
                    "total_tests": test_suite_result.total_tests if test_suite_result else 0,
                    "coverage_pct": test_suite_result.coverage.coverage_percentage if test_suite_result else 100.0,
                },
            ),
            "security": CategoryScore(
                category=QualityCategory.SECURITY,
                score=round(max(0.0, min(100.0, sec_score)), 2),
                weight=weights[QualityCategory.SECURITY],
                metrics={
                    "secrets": security_result.secrets_found if security_result else 0,
                    "sqli": security_result.sql_injections if security_result else 0,
                },
            ),
            "performance": CategoryScore(
                category=QualityCategory.PERFORMANCE,
                score=round(max(0.0, min(100.0, perf_score)), 2),
                weight=weights[QualityCategory.PERFORMANCE],
            ),
            "documentation": CategoryScore(
                category=QualityCategory.DOCUMENTATION,
                score=round(max(0.0, min(100.0, documentation_score)), 2),
                weight=weights[QualityCategory.DOCUMENTATION],
            ),
        }

        # Overall composite weighted average
        overall = sum(cs.score * cs.weight for cs in category_scores.values())

        # Letter grade
        if overall >= 95.0:
            grade = "A+"
        elif overall >= 90.0:
            grade = "A"
        elif overall >= 80.0:
            grade = "B"
        elif overall >= 70.0:
            grade = "C"
        elif overall >= 60.0:
            grade = "D"
        else:
            grade = "F"

        # Release Quality Gate Evaluation
        gate_reasons: List[str] = []
        passed_gate = True

        issues_list = all_issues or []
        critical_issues = len([i for i in issues_list if i.severity == IssueSeverity.CRITICAL])
        if security_result and not security_result.passed:
            passed_gate = False
            gate_reasons.append(f"Security gate failed: {len(security_result.vulnerabilities)} high/critical vulnerabilities found.")

        if test_suite_result is not None:
            if test_suite_result.failed > 0 or test_suite_result.errors > 0:
                passed_gate = False
                gate_reasons.append(f"Test suite has {test_suite_result.failed} failures and {test_suite_result.errors} errors.")
            if test_suite_result.coverage.coverage_percentage < self.MIN_COVERAGE_PCT:
                passed_gate = False
                gate_reasons.append(f"Test coverage ({test_suite_result.coverage.coverage_percentage:.1f}%) is below minimum threshold ({self.MIN_COVERAGE_PCT}%).")

        if architecture_score < self.MIN_ARCH_SCORE:
            passed_gate = False
            gate_reasons.append(f"Architecture score ({architecture_score:.1f}) is below threshold ({self.MIN_ARCH_SCORE}).")

        if code_quality_score < self.MIN_CODE_SCORE:
            passed_gate = False
            gate_reasons.append(f"Code quality score ({code_quality_score:.1f}) is below threshold ({self.MIN_CODE_SCORE}).")

        if overall < self.MIN_RELEASE_SCORE:
            passed_gate = False
            gate_reasons.append(f"Overall score ({overall:.1f}) is below release threshold ({self.MIN_RELEASE_SCORE}).")

        if critical_issues > 0:
            passed_gate = False
            gate_reasons.append(f"{critical_issues} critical bugs / issues remain unresolved.")

        suggestions: List[str] = []
        for r in gate_reasons:
            suggestions.append(f"Fix requirement: {r}")
        if not suggestions:
            suggestions.append("All release quality criteria satisfied. Code approved for production.")

        return QualityScore(
            overall_score=round(overall, 2),
            category_scores=category_scores,
            grade=grade,
            passed_gate=passed_gate,
            gate_reasons=gate_reasons,
            critical_issues_count=critical_issues,
            warnings_count=len([i for i in issues_list if i.severity != IssueSeverity.CRITICAL]),
            suggestions=suggestions,
        )
