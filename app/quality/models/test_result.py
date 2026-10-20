"""Test result and code coverage models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class TestType(str, Enum):
    UNIT = "unit"
    INTEGRATION = "integration"
    EDGE_CASE = "edge_case"
    REGRESSION = "regression"
    SMOKE = "smoke"


@dataclass
class TestCaseResult:
    name: str
    test_type: TestType = TestType.UNIT
    status: str = "PASSED"  # PASSED, FAILED, SKIPPED, ERROR
    duration_sec: float = 0.0
    error_message: str = ""
    traceback_str: str = ""
    file_path: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "test_type": self.test_type.value if isinstance(self.test_type, TestType) else str(self.test_type),
            "status": self.status,
            "duration_sec": round(float(self.duration_sec), 4),
            "error_message": self.error_message,
            "traceback_str": self.traceback_str,
            "file_path": self.file_path,
        }


@dataclass
class CoverageResult:
    total_statements: int = 0
    covered_statements: int = 0
    coverage_percentage: float = 100.0  # 0 to 100
    missing_lines_by_file: Dict[str, List[int]] = field(default_factory=dict)
    uncovered_branches: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_statements": self.total_statements,
            "covered_statements": self.covered_statements,
            "coverage_percentage": round(float(self.coverage_percentage), 2),
            "missing_lines_by_file": {k: list(v) for k, v in self.missing_lines_by_file.items()},
            "uncovered_branches": self.uncovered_branches,
        }


@dataclass
class TestSuiteResult:
    __test__ = False
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    skipped: int = 0
    test_cases: List[TestCaseResult] = field(default_factory=list)
    coverage: CoverageResult = field(default_factory=CoverageResult)
    duration_sec: float = 0.0
    success: bool = True
    failure_details: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_tests": self.total_tests,
            "passed": self.passed,
            "failed": self.failed,
            "errors": self.errors,
            "skipped": self.skipped,
            "test_cases": [tc.to_dict() for tc in self.test_cases],
            "coverage": self.coverage.to_dict(),
            "duration_sec": round(float(self.duration_sec), 4),
            "success": self.success,
            "failure_details": list(self.failure_details),
        }
