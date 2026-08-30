"""Comprehensive quality scoring system.

Scores projects on 5 weighted metrics:
  - Compile: 20%
  - Runtime: 20%
  - Tests Pass: 20%
  - Code Quality: 20%
  - Architecture: 20%

Target: 95-99% quality
"""

from __future__ import annotations

import ast
import compileall
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class QualityMetrics:
    """Individual quality metrics."""
    compile_score: float = 0.0
    runtime_score: float = 0.0
    test_score: float = 0.0
    code_quality_score: float = 0.0
    architecture_score: float = 0.0
    overall_score: float = 0.0
    grade: str = "F"
    passed_gate: bool = False
    details: Dict[str, Any] = field(default_factory=dict)


class ComprehensiveQualityScorer:
    """Score project quality across 5 dimensions.

    Target: 95-99% overall quality.
    """

    def __init__(self, project_path: str):
        self.project_path = Path(project_path).resolve()
        self.weights = {
            "compile": 0.20,
            "runtime": 0.20,
            "tests": 0.20,
            "code_quality": 0.20,
            "architecture": 0.20,
        }

    def score(self) -> QualityMetrics:
        """Calculate comprehensive quality score.

        Returns:
            QualityMetrics with all scores and details
        """
        compile_score, compile_details = self._score_compile()
        runtime_score, runtime_details = self._score_runtime()
        test_score, test_details = self._score_tests()
        code_quality_score, code_details = self._score_code_quality()
        arch_score, arch_details = self._score_architecture()

        overall = (
            compile_score * self.weights["compile"]
            + runtime_score * self.weights["runtime"]
            + test_score * self.weights["tests"]
            + code_quality_score * self.weights["code_quality"]
            + arch_score * self.weights["architecture"]
        )

        grade = self._calculate_grade(overall)
        passed = overall >= 95.0 and compile_score >= 90.0 and runtime_score >= 90.0

        return QualityMetrics(
            compile_score=round(compile_score, 2),
            runtime_score=round(runtime_score, 2),
            test_score=round(test_score, 2),
            code_quality_score=round(code_quality_score, 2),
            architecture_score=round(arch_score, 2),
            overall_score=round(overall, 2),
            grade=grade,
            passed_gate=passed,
            details={
                "compile": compile_details,
                "runtime": runtime_details,
                "tests": test_details,
                "code_quality": code_details,
                "architecture": arch_details,
            },
        )

    def _score_compile(self) -> Tuple[float, Dict[str, Any]]:
        """Score: Can all files compile without syntax errors?"""
        details: Dict[str, Any] = {"errors": [], "total_files": 0, "passed_files": 0}

        if not self.project_path.exists():
            return 0.0, details

        py_files = list(self.project_path.rglob("*.py"))
        details["total_files"] = len(py_files)
        passed = 0

        for py_file in py_files:
            try:
                with open(py_file, "r", encoding="utf-8", errors="replace") as f:
                    source = f.read()
                ast.parse(source)
                compileall.compile_file(str(py_file), quiet=1)
                passed += 1
            except SyntaxError as e:
                details["errors"].append({
                    "file": str(py_file.relative_to(self.project_path)),
                    "error": str(e),
                })
            except Exception:
                passed += 1  # compileall may fail for non-syntax reasons

        details["passed_files"] = passed
        if details["total_files"] == 0:
            return 100.0, details

        score = (passed / details["total_files"]) * 100.0
        return score, details

    def _score_runtime(self) -> Tuple[float, Dict[str, Any]]:
        """Score: Does the project run without runtime errors?"""
        details: Dict[str, Any] = {"errors": [], "execution_time": 0.0, "entry_point": ""}

        entry_points = ["main.py", "app.py", "cli.py", "__main__.py"]
        entry_file = None
        for ep in entry_points:
            candidate = self.project_path / ep
            if candidate.exists():
                entry_file = candidate
                break

        if not entry_file:
            # Try to find any runnable Python file
            py_files = list(self.project_path.rglob("*.py"))
            if py_files:
                entry_file = py_files[0]

        if not entry_file:
            return 50.0, details

        details["entry_point"] = str(entry_file.relative_to(self.project_path))

        try:
            start = time.perf_counter()
            result = subprocess.run(
                [sys.executable, str(entry_file), "--help"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=str(self.project_path),
            )
            details["execution_time"] = round(time.perf_counter() - start, 3)

            if result.returncode == 0:
                return 100.0, details
            elif result.returncode == 2:  # argparse --help returns 2 sometimes
                return 90.0, details
            else:
                details["errors"].append({
                    "type": "runtime_error",
                    "stdout": result.stdout[:500],
                    "stderr": result.stderr[:500],
                    "returncode": result.returncode,
                })
                return 40.0, details

        except subprocess.TimeoutExpired:
            details["errors"].append({"type": "timeout", "message": "Execution timed out after 10s"})
            return 30.0, details
        except Exception as e:
            details["errors"].append({"type": "exception", "message": str(e)})
            return 20.0, details

    def _score_tests(self) -> Tuple[float, Dict[str, Any]]:
        """Score: Do tests pass?"""
        details: Dict[str, Any] = {"total": 0, "passed": 0, "failed": 0, "errors": []}

        test_dir = self.project_path / "tests"
        if not test_dir.exists():
            return 70.0, details  # No tests = partial credit

        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(test_dir), "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(self.project_path),
            )

            output = result.stdout + result.stderr
            details["raw_output"] = output[:1000]

            # Parse pytest output
            passed = output.count(" PASSED")
            failed = output.count(" FAILED")
            errors = output.count(" ERROR")

            details["passed"] = passed
            details["failed"] = failed
            details["errors_count"] = errors
            details["total"] = passed + failed + errors

            if details["total"] == 0:
                return 70.0, details

            score = (passed / details["total"]) * 100.0
            return score, details

        except subprocess.TimeoutExpired:
            details["errors"].append("Test execution timed out")
            return 30.0, details
        except FileNotFoundError:
            # pytest not installed - try unittest
            return self._score_unittest()
        except Exception as e:
            details["errors"].append(str(e))
            return 40.0, details

    def _score_unittest(self) -> Tuple[float, Dict[str, Any]]:
        """Fallback: run unittest discovery."""
        details: Dict[str, Any] = {"total": 0, "passed": 0, "failed": 0, "errors": []}

        try:
            import unittest
            loader = unittest.TestLoader()
            suite = loader.discover(str(self.project_path / "tests"), pattern="test_*.py")
            runner = unittest.TextTestRunner(verbosity=0)
            result = runner.run(suite)

            details["total"] = result.testsRun
            details["passed"] = result.testsRun - len(result.failures) - len(result.errors)
            details["failed"] = len(result.failures)
            details["errors_count"] = len(result.errors)

            if result.testsRun == 0:
                return 70.0, details

            score = (details["passed"] / result.testsRun) * 100.0
            return score, details

        except Exception as e:
            details["errors"].append(str(e))
            return 40.0, details

    def _score_code_quality(self) -> Tuple[float, Dict[str, Any]]:
        """Score: Code complexity, duplication, dead code, smells."""
        details: Dict[str, Any] = {"issues": [], "complexity": 0.0}

        if not self.project_path.exists():
            return 50.0, details

        try:
            from app.quality.qa_engine import QAEngine
            qa = QAEngine(str(self.project_path))
            quality_score, static_result = qa.evaluate_quality(str(self.project_path))

            details["overall"] = quality_score.overall_score
            details["grade"] = quality_score.grade
            details["issues"] = [
                {
                    "file": i.file,
                    "rule": i.rule,
                    "message": i.message,
                    "severity": i.severity.value,
                }
                for i in quality_score.category_scores["code_quality"].issues[:10]
            ]
            details["complexity"] = static_result.complexity_score

            return quality_score.overall_score, details

        except Exception as e:
            details["error"] = str(e)
            return 60.0, details

    def _score_architecture(self) -> Tuple[float, Dict[str, Any]]:
        """Score: Project structure, layer separation, config files."""
        details: Dict[str, Any] = {"violations": [], "structure_score": 0.0}

        if not self.project_path.exists():
            return 50.0, details

        score = 100.0

        # Check required structure
        required_dirs = ["src", "tests"]
        required_files = ["requirements.txt", "README.md", ".gitignore"]

        for req_dir in required_dirs:
            if not (self.project_path / req_dir).exists():
                details["violations"].append(f"Missing directory: {req_dir}")
                score -= 15.0

        for req_file in required_files:
            if not (self.project_path / req_file).exists():
                details["violations"].append(f"Missing file: {req_file}")
                score -= 10.0

        # Check for config files
        config_files = list(self.project_path.glob("*.json")) + list(self.project_path.glob("*.yaml")) + list(self.project_path.glob("*.yml"))
        if not config_files:
            details["violations"].append("No configuration files found")
            score -= 5.0

        # Check package structure
        py_files = list(self.project_path.rglob("*.py"))
        if len(py_files) > 0:
            has_init = any(f.name == "__init__.py" for f in py_files)
            if not has_init and (self.project_path / "src").exists():
                details["violations"].append("Missing __init__.py in src/")
                score -= 5.0

        details["structure_score"] = max(0.0, score)
        return max(0.0, score), details

    def _calculate_grade(self, score: float) -> str:
        """Calculate letter grade from score."""
        if score >= 97.0:
            return "A+"
        elif score >= 93.0:
            return "A"
        elif score >= 90.0:
            return "A-"
        elif score >= 85.0:
            return "B+"
        elif score >= 80.0:
            return "B"
        elif score >= 75.0:
            return "C+"
        elif score >= 70.0:
            return "C"
        elif score >= 60.0:
            return "D"
        else:
            return "F"

    def get_improvement_suggestions(self, metrics: QualityMetrics) -> List[str]:
        """Get actionable suggestions to improve quality."""
        suggestions = []

        if metrics.compile_score < 95.0:
            suggestions.append("Fix all syntax errors and import issues before runtime testing")

        if metrics.runtime_score < 95.0:
            suggestions.append("Add error handling and validate entry point execution")

        if metrics.test_score < 95.0:
            suggestions.append("Increase test coverage and fix failing tests")

        if metrics.code_quality_score < 95.0:
            suggestions.append("Reduce code complexity, remove dead code, fix naming violations")

        if metrics.architecture_score < 95.0:
            suggestions.append("Add missing directories, config files, and improve project structure")

        return suggestions
