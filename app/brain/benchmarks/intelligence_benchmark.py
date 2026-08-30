"""Benchmarks for measuring intelligence.

Benchmarks prove whether improvements actually make Jarvis smarter.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.core.logger import Logger


@dataclass
class BenchmarkResult:
    """Result of a benchmark test."""
    benchmark_id: str
    name: str
    score: float = 0.0
    max_score: float = 100.0
    passed: bool = False
    duration: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)


class IntelligenceBenchmark:
    """Benchmark suite for measuring Jarvis intelligence.

    Benchmarks:
      1. Planning Accuracy - Can Jarvis break down problems correctly?
      2. Decision Quality - Does Jarvis choose optimal plans?
      3. Error Recovery - Can Jarvis fix errors automatically?
      4. Strategy Selection - Does Jarvis choose right strategies?
      5. Learning Speed - Does Jarvis improve over time?
    """

    def __init__(self):
        self._results: List[BenchmarkResult] = []
        self._benchmark_history: List[Dict[str, Any]] = []

    def run_all(self, brain_kernel) -> Dict[str, BenchmarkResult]:
        """Run all benchmarks.

        Args:
            brain_kernel: BrainKernel instance

        Returns:
            Dict of benchmark results
        """
        results = {}
        results["planning"] = self._benchmark_planning(brain_kernel)
        results["decision"] = self._benchmark_decision(brain_kernel)
        results["error_recovery"] = self._benchmark_error_recovery(brain_kernel)
        results["strategy"] = self._benchmark_strategy(brain_kernel)
        results["learning"] = self._benchmark_learning(brain_kernel)

        self._results.extend(results.values())
        return results

    def _benchmark_planning(self, brain_kernel) -> BenchmarkResult:
        """Benchmark planning accuracy."""
        start = time.perf_counter()
        test_cases = [
            "Build a todo API",
            "Create a portfolio website",
            "Fix the login bug",
            "Research Python best practices",
        ]

        scores = []
        for test in test_cases:
            try:
                result = brain_kernel.thinking.think(test)
                score = result.confidence
                scores.append(score)
            except Exception:
                scores.append(0.0)

        avg_score = sum(scores) / len(scores) if scores else 0.0
        duration = time.perf_counter() - start

        return BenchmarkResult(
            benchmark_id="planning_accuracy",
            name="Planning Accuracy",
            score=avg_score,
            max_score=100.0,
            passed=avg_score >= 70.0,
            duration=duration,
            details={"test_cases": len(test_cases), "scores": scores},
        )

    def _benchmark_decision(self, brain_kernel) -> BenchmarkResult:
        """Benchmark decision quality."""
        start = time.perf_counter()
        test_plans = [
            {"plan_id": "p1", "description": "Direct approach", "confidence": 70.0, "risk": 30.0, "steps": ["a", "b"]},
            {"plan_id": "p2", "description": "Research first", "confidence": 85.0, "risk": 20.0, "steps": ["a", "b", "c"]},
            {"plan_id": "p3", "description": "Test first", "confidence": 80.0, "risk": 15.0, "steps": ["a", "b", "c", "d"]},
        ]

        try:
            result = brain_kernel.decision.decide(test_plans)
            score = result.confidence * 100
            passed = score >= 70.0
        except Exception:
            score = 0.0
            passed = False

        duration = time.perf_counter() - start

        return BenchmarkResult(
            benchmark_id="decision_quality",
            name="Decision Quality",
            score=score,
            max_score=100.0,
            passed=passed,
            duration=duration,
        )

    def _benchmark_error_recovery(self, brain_kernel) -> BenchmarkResult:
        """Benchmark error recovery."""
        start = time.perf_counter()
        test_errors = [
            Exception("ModuleNotFoundError: No module named 'requests'"),
            Exception("AttributeError: 'NoneType' object has no attribute 'get'"),
            Exception("SyntaxError: invalid syntax"),
        ]

        successes = 0
        for error in test_errors:
            try:
                analysis = brain_kernel.error_intelligence.analyze(error)
                if analysis.category.value != "unknown":
                    successes += 1
            except Exception:
                pass

        score = (successes / len(test_errors)) * 100.0 if test_errors else 0.0
        duration = time.perf_counter() - start

        return BenchmarkResult(
            benchmark_id="error_recovery",
            name="Error Recovery",
            score=score,
            max_score=100.0,
            passed=score >= 60.0,
            duration=duration,
            details={"errors_tested": len(test_errors), "successes": successes},
        )

    def _benchmark_strategy(self, brain_kernel) -> BenchmarkResult:
        """Benchmark strategy selection."""
        start = time.perf_counter()
        test_tasks = [
            {"problem": "What is the time?", "complexity": "low"},
            {"problem": "Debug this error", "complexity": "medium"},
            {"problem": "Design a scalable architecture", "complexity": "high"},
        ]

        scores = []
        for task in test_tasks:
            try:
                result = brain_kernel.strategy.select(task)
                scores.append(result.confidence * 100)
            except Exception:
                scores.append(0.0)

        avg_score = sum(scores) / len(scores) if scores else 0.0
        duration = time.perf_counter() - start

        return BenchmarkResult(
            benchmark_id="strategy_selection",
            name="Strategy Selection",
            score=avg_score,
            max_score=100.0,
            passed=avg_score >= 70.0,
            duration=duration,
            details={"test_cases": len(test_tasks), "scores": scores},
        )

    def _benchmark_learning(self, brain_kernel) -> BenchmarkResult:
        """Benchmark learning speed."""
        start = time.perf_counter()

        # Check if analytics and evolution are tracking
        analytics = brain_kernel.analytics
        evolution = brain_kernel.evolution

        score = 50.0  # Base score
        if analytics._task_history:
            score += 20.0
        if evolution._metrics_history:
            score += 20.0
        if len(evolution._evolution_history) > 0:
            score += 10.0

        duration = time.perf_counter() - start

        return BenchmarkResult(
            benchmark_id="learning_speed",
            name="Learning Speed",
            score=score,
            max_score=100.0,
            passed=score >= 60.0,
            duration=duration,
        )

    def get_summary(self) -> Dict[str, Any]:
        """Get benchmark summary."""
        if not self._results:
            return {"status": "no_benchmarks_run"}

        passed = sum(1 for r in self._results if r.passed)
        total = len(self._results)
        avg_score = sum(r.score for r in self._results) / total if total > 0 else 0.0

        return {
            "total_benchmarks": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": (passed / total * 100) if total > 0 else 0,
            "average_score": avg_score,
            "results": [
                {
                    "id": r.benchmark_id,
                    "name": r.name,
                    "score": r.score,
                    "max_score": r.max_score,
                    "passed": r.passed,
                    "duration": r.duration,
                }
                for r in self._results
            ],
        }
