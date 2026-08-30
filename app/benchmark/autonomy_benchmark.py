"""Repeatable autonomy benchmark definitions and scoring."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List


@dataclass(frozen=True)
class AutonomyBenchmark:
    identifier: str
    title: str
    prompt: str
    tier: str
    criteria: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.identifier, "title": self.title, "prompt": self.prompt,
                "tier": self.tier, "criteria": list(self.criteria)}


class AutonomyBenchmarkCatalog:
    """Stable benchmark catalog for capability and reliability comparisons."""

    BENCHMARKS = (
        AutonomyBenchmark("todo-app", "Todo App", "Build a Todo application", "basic",
                          ("requirements", "architecture", "implementation", "tests")),
        AutonomyBenchmark("hospital", "Hospital Management", "Build a Hospital Management System", "intermediate",
                          ("requirements", "architecture", "database", "tests", "documentation")),
        AutonomyBenchmark("crm", "CRM", "Build a CRM application", "intermediate",
                          ("requirements", "architecture", "api", "tests", "documentation")),
        AutonomyBenchmark("food-delivery", "Food Delivery", "Build a food delivery platform", "advanced",
                          ("requirements", "architecture", "payments", "tests", "deployment")),
        AutonomyBenchmark("multi-tenant-saas", "Multi-tenant SaaS", "Build a multi-tenant SaaS platform", "advanced",
                          ("requirements", "architecture", "isolation", "security", "deployment")),
        AutonomyBenchmark("large-repo-change", "Large Repository Change", "Modify an existing 100k line project", "expert",
                          ("repository_analysis", "implementation", "tests", "review")),
        AutonomyBenchmark("unknown-repo-feature", "Unknown Repository Feature", "Understand an unknown repository and add a feature", "expert",
                          ("repository_analysis", "architecture", "implementation", "tests")),
        AutonomyBenchmark("production-bug", "Production Bug Fix", "Detect and fix a production bug", "expert",
                          ("reproduction", "root_cause", "repair", "regression_tests")),
        AutonomyBenchmark("architecture-review", "Architecture Review", "Review an existing software architecture", "advanced",
                          ("analysis", "risks", "recommendations", "report")),
        AutonomyBenchmark("self-improvement", "Self Improvement", "Improve the previous project strategy", "expert",
                          ("baseline", "experiment", "comparison", "learning")),
    )

    def list(self, tier: str | None = None) -> List[AutonomyBenchmark]:
        if tier is None:
            return list(self.BENCHMARKS)
        return [item for item in self.BENCHMARKS if item.tier == tier.casefold()]

    def get(self, identifier: str) -> AutonomyBenchmark | None:
        return next((item for item in self.BENCHMARKS if item.identifier == identifier.casefold()), None)


class AutonomyBenchmarkRunner:
    """Execute injected handlers and score automation without hiding intervention."""

    def __init__(self, catalog=None):
        self.catalog = catalog or AutonomyBenchmarkCatalog()

    def run(self, handler, tier: str | None = None) -> Dict[str, Any]:
        if not callable(handler):
            raise TypeError("Benchmark handler must be callable")
        results = []
        for benchmark in self.catalog.list(tier):
            started = datetime.now(timezone.utc)
            outcome = handler(benchmark)
            if not isinstance(outcome, dict):
                raise TypeError(f"Handler result for {benchmark.identifier} must be a dictionary")
            criteria = outcome.get("criteria", {})
            passed = [name for name in benchmark.criteria if bool(criteria.get(name))]
            intervention = max(0.0, min(1.0, float(outcome.get("manual_intervention", 0.0))))
            success = bool(outcome.get("success")) and len(passed) == len(benchmark.criteria)
            results.append({
                "benchmark": benchmark.to_dict(),
                "success": success,
                "criteria_passed": passed,
                "criteria_total": len(benchmark.criteria),
                "manual_intervention": intervention,
                "automation_rate": round(1.0 - intervention, 4),
                "duration_seconds": max(0.0, (datetime.now(timezone.utc) - started).total_seconds()),
                "outcome": dict(outcome),
            })
        total = len(results)
        return {
            "kind": "autonomy_benchmark",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "total": total,
            "successful": sum(item["success"] for item in results),
            "success_rate": round(sum(item["success"] for item in results) / total, 4) if total else 0.0,
            "automation_rate": round(sum(item["automation_rate"] for item in results) / total, 4) if total else 0.0,
            "results": results,
        }

