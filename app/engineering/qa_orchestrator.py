"""QA Orchestrator for autonomous execution.

Runs a quality assurance loop:
  Static Analysis → Tests → Repair → Repeat
until quality threshold is met or max cycles reached.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.core.logger import Logger
from app.core.results import ExecutionResult
from app.quality.qa_engine import StaticAnalyzer
from app.quality.test_engine import TestEngine
from app.quality.repair_engine import RepairEngine
from app.quality.models.quality_result import QualityScore, StaticAnalysisResult


@dataclass
class QACycleResult:
    """Result of a single QA cycle."""

    cycle: int = 0
    static_analysis_passed: bool = False
    tests_passed: bool = False
    issues_found: int = 0
    issues_fixed: int = 0
    quality_score: float = 0.0
    duration: float = 0.0
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "cycle": self.cycle,
            "static_analysis_passed": self.static_analysis_passed,
            "tests_passed": self.tests_passed,
            "issues_found": self.issues_found,
            "issues_fixed": self.issues_fixed,
            "quality_score": round(self.quality_score, 1),
            "duration": round(self.duration, 2),
            "errors": list(self.errors),
        }


@dataclass
class QAReport:
    """Complete QA report after all cycles."""

    project_path: str = ""
    total_cycles: int = 0
    total_issues_found: int = 0
    total_issues_fixed: int = 0
    final_quality_score: float = 0.0
    static_analysis_passed: bool = False
    tests_passed: bool = False
    cycles: List[QACycleResult] = field(default_factory=list)
    success: bool = False
    duration: float = 0.0

    def to_dict(self) -> dict:
        return {
            "project_path": self.project_path,
            "total_cycles": self.total_cycles,
            "total_issues_found": self.total_issues_found,
            "total_issues_fixed": self.total_issues_fixed,
            "final_quality_score": round(self.final_quality_score, 1),
            "static_analysis_passed": self.static_analysis_passed,
            "tests_passed": self.tests_passed,
            "success": self.success,
            "duration": round(self.duration, 2),
            "cycles": [c.to_dict() for c in self.cycles],
        }


class QAOrchestrator:
    """Orchestrate quality assurance cycles.

    Runs static analysis, tests, and repair in a loop until
    quality threshold is met or max cycles is reached.
    """

    def __init__(
        self,
        quality_threshold: float = 80.0,
        max_cycles: int = 3,
        static_analyzer=None,
        test_engine=None,
        repair_engine=None,
    ):
        self.quality_threshold = quality_threshold
        self.max_cycles = max_cycles
        self.static_analyzer = static_analyzer or StaticAnalyzer()
        self.test_engine = test_engine or TestEngine()
        self.repair_engine = repair_engine or RepairEngine()

    def run(self, project_path: str) -> QAReport:
        """Run QA loop on a project.

        Args:
            project_path: Path to the project to validate.

        Returns:
            QAReport with complete QA results.
        """
        started = time.perf_counter()
        report = QAReport(project_path=project_path)

        Logger.info(f"[QAOrchestrator] Starting QA loop for: {project_path}")

        for cycle in range(1, self.max_cycles + 1):
            cycle_start = time.perf_counter()
            cycle_result = QACycleResult(cycle=cycle)

            # Static analysis
            static_result = self._run_static_analysis(project_path)
            cycle_result.static_analysis_passed = static_result.get("passed", False)
            cycle_result.issues_found = len(static_result.get("issues", []))

            # Tests
            test_passed, test_output = self._run_tests(project_path)
            cycle_result.tests_passed = test_passed

            # Calculate quality score
            static_score = 100.0 if cycle_result.static_analysis_passed else max(0, 100 - cycle_result.issues_found * 10)
            test_score = 100.0 if test_passed else 50.0
            cycle_result.quality_score = (static_score + test_score) / 2

            # Repair if needed
            if not cycle_result.static_analysis_passed or not test_passed:
                issues = static_result.get("issues", [])
                if issues:
                    fixed = self._run_repair(project_path, issues)
                    cycle_result.issues_fixed = fixed
                    report.total_issues_fixed += fixed

            report.total_issues_found += cycle_result.issues_found
            cycle_result.duration = time.perf_counter() - cycle_start
            report.cycles.append(cycle_result)

            Logger.info(
                f"[QAOrchestrator] Cycle {cycle}: "
                f"static={'PASS' if cycle_result.static_analysis_passed else 'FAIL'} "
                f"tests={'PASS' if cycle_result.tests_passed else 'FAIL'} "
                f"score={cycle_result.quality_score:.1f}"
            )

            # Check if quality threshold met
            if (cycle_result.quality_score >= self.quality_threshold and cycle_result.static_analysis_passed and cycle_result.tests_passed):
                report.success = True
                report.total_cycles = cycle
                break

        # Final status
        report.final_quality_score = report.cycles[-1].quality_score if report.cycles else 0.0
        report.static_analysis_passed = report.cycles[-1].static_analysis_passed if report.cycles else False
        report.tests_passed = report.cycles[-1].tests_passed if report.cycles else False
        report.total_cycles = len(report.cycles)
        report.duration = time.perf_counter() - started
        report.success = (report.final_quality_score >= self.quality_threshold and report.static_analysis_passed and report.tests_passed)

        Logger.success(
            f"[QAOrchestrator] QA complete: {report.total_cycles} cycles, "
            f"score={report.final_quality_score:.1f}, fixed={report.total_issues_fixed}"
        )

        return report

    def _run_static_analysis(self, project_path: str) -> Dict[str, Any]:
        """Run static analysis."""
        try:
            self.static_analyzer.root_path = project_path
            result = self.static_analyzer.scan_directory()
            issues = []
            if hasattr(result, "issues"):
                for issue in result.issues:
                    issues.append({
                        "category": issue.category.value if hasattr(issue.category, "value") else str(issue.category),
                        "severity": issue.severity.value if hasattr(issue.severity, "value") else str(issue.severity),
                        "message": issue.message,
                        "file": getattr(issue, "file_path", ""),
                        "line": getattr(issue, "line_number", 0),
                    })
            passed = len(issues) == 0
            return {"passed": passed, "issues": issues, "result": result}
        except Exception as exc:
            Logger.error(f"[QAOrchestrator] Static analysis failed: {exc}")
            return {"passed": False, "issues": [], "error": str(exc)}

    def _run_tests(self, project_path: str) -> tuple[bool, str]:
        """Run tests."""
        try:
            result = self.test_engine.run(project_path)
            passed = getattr(result, "success", False) or getattr(result, "passed", False)
            output = getattr(result, "output", "") or getattr(result, "message", "")
            return passed, str(output)
        except Exception as exc:
            Logger.error(f"[QAOrchestrator] Tests failed: {exc}")
            return False, str(exc)

    def _run_repair(self, project_path: str, issues: List[Dict[str, Any]]) -> int:
        """Run repair on issues."""
        try:
            repaired = 0
            for issue in issues[:10]:  # Limit per cycle
                result = self.repair_engine.repair(project_path, issue)
                if result and getattr(result, "success", False):
                    repaired += 1
            return repaired
        except Exception as exc:
            Logger.error(f"[QAOrchestrator] Repair failed: {exc}")
            return 0
