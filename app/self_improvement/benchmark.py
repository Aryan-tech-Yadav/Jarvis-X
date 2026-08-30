"""Benchmark engine for self-improvement comparison.

Runs benchmarks on code versions and compares before/after metrics.
"""

from __future__ import annotations

import ast
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.logger import Logger


@dataclass
class BenchmarkResult:
    """Benchmark result for a code version."""

    version: str
    path: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    quality_score: float = 0.0
    complexity_score: float = 0.0
    total_lines: int = 0
    python_files: int = 0
    issues_count: int = 0
    critical_issues: int = 0
    high_issues: int = 0
    medium_issues: int = 0
    low_issues: int = 0
    test_coverage: float = 0.0
    execution_time: float = 0.0
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "path": self.path,
            "timestamp": self.timestamp,
            "quality_score": round(self.quality_score, 2),
            "complexity_score": round(self.complexity_score, 2),
            "total_lines": self.total_lines,
            "python_files": self.python_files,
            "issues_count": self.issues_count,
            "critical_issues": self.critical_issues,
            "high_issues": self.high_issues,
            "medium_issues": self.medium_issues,
            "low_issues": self.low_issues,
            "test_coverage": round(self.test_coverage, 2),
            "execution_time": round(self.execution_time, 3),
            "metrics": dict(self.metrics),
        }


class BenchmarkEngine:
    """Run benchmarks on code and compare versions."""

    def __init__(self, project_path: str = "."):
        self.project_path = os.path.abspath(project_path)

    def run_benchmark(self, path: str, version: str = "current") -> BenchmarkResult:
        """Run benchmark on a project path."""
        started = time.perf_counter()
        Logger.info(f"[BenchmarkEngine] Running benchmark on: {path}")
        
        result = BenchmarkResult(version=version, path=path)
        
        try:
            # Use existing QA engine
            from app.quality.qa_engine import QAEngine
            qa = QAEngine(path)
            quality_score, static_result = qa.evaluate_quality(path)
            
            result.quality_score = quality_score.overall_score
            result.complexity_score = static_result.complexity_score
            result.issues_count = len(static_result.issues)
            result.critical_issues = quality_score.critical_issues_count
            result.high_issues = len([i for i in static_result.issues if i.severity.value == "high"])
            result.medium_issues = len([i for i in static_result.issues if i.severity.value == "medium"])
            result.low_issues = len([i for i in static_result.issues if i.severity.value == "low"])
            
            # File metrics
            py_files = self._count_python_files(path)
            result.python_files = py_files["count"]
            result.total_lines = py_files["lines"]
            
            # Test coverage estimation
            result.test_coverage = self._estimate_test_coverage(path)
            
        except Exception as exc:
            Logger.error(f"[BenchmarkEngine] Benchmark failed: {exc}")
        
        result.execution_time = time.perf_counter() - started
        Logger.success(f"[BenchmarkEngine] Benchmark complete: score={result.quality_score:.2f}")
        return result

    def compare(self, before: BenchmarkResult, after: BenchmarkResult) -> Dict[str, Any]:
        """Compare two benchmark results."""
        comparison = {
            "before": before.to_dict(),
            "after": after.to_dict(),
            "improvements": [],
            "regressions": [],
            "neutral": [],
            "overall_change": 0.0,
            "recommendation": "",
        }
        
        # Quality score change
        quality_change = after.quality_score - before.quality_score
        comparison["overall_change"] = round(quality_change, 2)
        
        # Compare metrics
        metrics_to_compare = [
            ("quality_score", "Quality Score", True),
            ("complexity_score", "Complexity Score", True),
            ("issues_count", "Issues Count", False),
            ("critical_issues", "Critical Issues", False),
            ("high_issues", "High Issues", False),
            ("medium_issues", "Medium Issues", False),
            ("low_issues", "Low Issues", False),
            ("total_lines", "Total Lines", True),  # Lower is not always better
            ("test_coverage", "Test Coverage", True),
        ]
        
        for key, label, higher_is_better in metrics_to_compare:
            before_val = getattr(before, key, 0)
            after_val = getattr(after, key, 0)
            change = after_val - before_val
            
            if higher_is_better:
                if change > 0:
                    comparison["improvements"].append(f"{label}: {before_val} -> {after_val} (+{change})")
                elif change < 0:
                    comparison["regressions"].append(f"{label}: {before_val} -> {after_val} ({change})")
                else:
                    comparison["neutral"].append(f"{label}: unchanged ({before_val})")
            else:
                if change < 0:
                    comparison["improvements"].append(f"{label}: {before_val} -> {after_val} ({change})")
                elif change > 0:
                    comparison["regressions"].append(f"{label}: {before_val} -> {after_val} (+{change})")
                else:
                    comparison["neutral"].append(f"{label}: unchanged ({before_val})")
        
        # Recommendation
        if quality_change > 5:
            comparison["recommendation"] = "STRONG_ACCEPT"
        elif quality_change > 0:
            comparison["recommendation"] = "ACCEPT"
        elif quality_change > -5:
            comparison["recommendation"] = "REVIEW"
        else:
            comparison["recommendation"] = "REJECT"
        
        return comparison

    def _count_python_files(self, path: str) -> Dict[str, int]:
        """Count Python files and lines."""
        count = 0
        lines = 0
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d not in {".git", ".venv", "venv", "__pycache__"}]
            for filename in files:
                if filename.endswith(".py"):
                    count += 1
                    try:
                        with open(os.path.join(root, filename), "r", encoding="utf-8", errors="replace") as f:
                            lines += len(f.read().splitlines())
                    except (OSError, UnicodeDecodeError):
                        continue
        return {"count": count, "lines": lines}

    def _estimate_test_coverage(self, path: str) -> float:
        """Estimate test coverage."""
        test_files = 0
        total_files = 0
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d not in {".git", ".venv", "venv", "__pycache__"}]
            for filename in files:
                if filename.endswith(".py"):
                    total_files += 1
                    if "test" in filename.lower() or "tests" in root.lower():
                        test_files += 1
        
        if total_files == 0:
            return 0.0
        return round((test_files / total_files) * 100.0, 2)
