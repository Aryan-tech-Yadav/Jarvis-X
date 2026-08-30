"""Benchmark tracking and comparison for project execution.

Tracks performance benchmarks across project executions:
  - execution time
  - throughput
  - resource utilization
  - comparison against baselines

Example output:
  Benchmark          Baseline    Current    Delta
  Execution Time     120.5s      98.3s      -18.4%
  Memory Usage       256MB       198MB      -22.7%
  LLM Calls          145         112        -22.8%
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class BenchmarkResult:
    """Single benchmark measurement."""

    name: str = ""
    value: float = 0.0
    unit: str = ""
    category: str = "general"  # general, performance, resource, cost
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "category": self.category,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }


@dataclass
class BenchmarkComparison:
    """Comparison between baseline and current benchmark."""

    name: str = ""
    baseline_value: float = 0.0
    current_value: float = 0.0
    unit: str = ""
    delta: float = 0.0
    delta_pct: float = 0.0
    improved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "baseline_value": self.baseline_value,
            "current_value": self.current_value,
            "unit": self.unit,
            "delta": round(self.delta, 3),
            "delta_pct": round(self.delta_pct, 2),
            "improved": self.improved,
        }


class BenchmarkTracker:
    """Track and compare performance benchmarks."""

    def __init__(self, benchmarks_path: str = os.path.join("data", "benchmarks.json")):
        self.benchmarks_path = benchmarks_path
        self._benchmarks: Dict[str, List[BenchmarkResult]] = {}
        self._load()

    def _load(self):
        if os.path.isfile(self.benchmarks_path):
            try:
                with open(self.benchmarks_path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                if isinstance(raw, dict):
                    for name, results in raw.items():
                        self._benchmarks[name] = [
                            BenchmarkResult(**r) for r in results if isinstance(r, dict)
                        ]
            except (OSError, json.JSONDecodeError, TypeError):
                pass

    def _save(self):
        os.makedirs(os.path.dirname(self.benchmarks_path), exist_ok=True)
        payload = {
            name: [r.to_dict() for r in results]
            for name, results in self._benchmarks.items()
        }
        with open(self.benchmarks_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, default=str)

    def record(self, name: str, value: float, unit: str = "",
               category: str = "general", metadata: Optional[Dict[str, Any]] = None) -> BenchmarkResult:
        """Record a benchmark measurement."""
        result = BenchmarkResult(
            name=name,
            value=value,
            unit=unit,
            category=category,
            metadata=metadata or {},
        )
        if name not in self._benchmarks:
            self._benchmarks[name] = []
        self._benchmarks[name].append(result)
        self._save()
        return result

    def record_execution_time(self, seconds: float) -> BenchmarkResult:
        """Record execution time benchmark."""
        return self.record("execution_time", seconds, unit="seconds", category="performance")

    def record_memory_usage(self, mb: float) -> BenchmarkResult:
        """Record memory usage benchmark."""
        return self.record("memory_usage", mb, unit="MB", category="resource")

    def record_llm_calls(self, count: int) -> BenchmarkResult:
        """Record LLM call count benchmark."""
        return self.record("llm_calls", float(count), unit="calls", category="cost")

    def record_throughput(self, items_per_second: float) -> BenchmarkResult:
        """Record throughput benchmark."""
        return self.record("throughput", items_per_second, unit="items/s", category="performance")

    def record_cost(self, dollars: float) -> BenchmarkResult:
        """Record cost benchmark."""
        return self.record("cost_estimate", dollars, unit="USD", category="cost")

    def get_latest(self, name: str) -> Optional[BenchmarkResult]:
        """Get the latest benchmark for a name."""
        results = self._benchmarks.get(name, [])
        return results[-1] if results else None

    def get_history(self, name: str) -> List[BenchmarkResult]:
        """Get full history for a benchmark name."""
        return list(self._benchmarks.get(name, []))

    def compare_with_baseline(self, name: str, baseline: float) -> Optional[BenchmarkComparison]:
        """Compare latest benchmark against a baseline value."""
        latest = self.get_latest(name)
        if not latest:
            return None

        delta = latest.value - baseline
        delta_pct = (delta / abs(baseline)) * 100 if baseline != 0 else 0.0

        improved = False
        if name in ("execution_time", "memory_usage", "llm_calls", "cost_estimate", "repair_count"):
            improved = delta < 0
        elif name in ("throughput", "coverage", "quality", "success_rate"):
            improved = delta > 0

        return BenchmarkComparison(
            name=name,
            baseline_value=baseline,
            current_value=latest.value,
            unit=latest.unit,
            delta=delta,
            delta_pct=delta_pct,
            improved=improved,
        )

    def compare_all(self, baselines: Dict[str, float]) -> List[BenchmarkComparison]:
        """Compare all benchmarks against provided baselines."""
        comparisons = []
        for name, baseline in baselines.items():
            comp = self.compare_with_baseline(name, baseline)
            if comp:
                comparisons.append(comp)
        return comparisons

    def summary(self) -> Dict[str, Any]:
        """Get summary of all benchmarks."""
        latest = {}
        for name, results in self._benchmarks.items():
            if results:
                latest[name] = {
                    "value": results[-1].value,
                    "unit": results[-1].unit,
                    "category": results[-1].category,
                    "measurements": len(results),
                }
        return {
            "benchmarks": latest,
            "total_benchmarks": len(self._benchmarks),
            "total_measurements": sum(len(r) for r in self._benchmarks.values()),
        }

    def format_report(self, baselines: Optional[Dict[str, float]] = None) -> str:
        """Format a human-readable benchmark report."""
        lines = ["Benchmark Report", "=" * 60]

        if baselines:
            comparisons = self.compare_all(baselines)
            lines.append(f"{'Benchmark':<20} {'Baseline':>12} {'Current':>12} {'Delta':>12}")
            lines.append("-" * 60)
            for comp in comparisons:
                delta_str = f"{comp.delta_pct:+.1f}%"
                arrow = "+" if comp.improved else "-"
                lines.append(
                    f"{comp.name:<20} {comp.baseline_value:>12.2f} "
                    f"{comp.current_value:>12.2f} {delta_str:>11}{arrow}"
                )
        else:
            lines.append(f"{'Benchmark':<20} {'Value':>12} {'Unit':>10}")
            lines.append("-" * 60)
            for name, results in self._benchmarks.items():
                if results:
                    latest = results[-1]
                    lines.append(f"{name:<20} {latest.value:>12.2f} {latest.unit:>10}")

        return "\n".join(lines)
