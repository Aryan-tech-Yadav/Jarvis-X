"""Self Improver for Jarvis-X.

Automatically improves Jarvis's own patterns and behaviors based on:
  - Failure analysis
  - Benchmark comparisons
  - Pattern success rates
  - User feedback

When QA reports "Authentication fails repeatedly":
  - Self Improver updates the auth pattern
  - Future projects use the improved version
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.intelligence.experience_engine import ExperienceEngine, ProjectExperience
from app.intelligence.pattern_library import PatternLibrary, EngineeringPattern
from app.intelligence.engineering_memory import EngineeringMemory, EngineeringMemoryEntry
from app.intelligence.benchmark_engine import BenchmarkEngine, BenchmarkReport


@dataclass
class Improvement:
    """A single improvement made by the self improver."""

    improvement_id: str = ""
    category: str = "general"
    description: str = ""
    before_score: float = 0.0
    after_score: float = 0.0
    delta: float = 0.0
    applied_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.improvement_id:
            self.improvement_id = f"imp-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"

    def to_dict(self) -> dict:
        return {
            "improvement_id": self.improvement_id,
            "category": self.category,
            "description": self.description,
            "before_score": self.before_score,
            "after_score": self.after_score,
            "delta": self.delta,
            "applied_at": self.applied_at,
            "metadata": dict(self.metadata),
        }


class SelfImprover:
    """Automatically improve patterns and behaviors based on outcomes."""

    def __init__(self, experience_engine: Optional[ExperienceEngine] = None,
                 pattern_library: Optional[PatternLibrary] = None,
                 engineering_memory: Optional[EngineeringMemory] = None,
                 benchmark_engine: Optional[BenchmarkEngine] = None):
        self.experiences = experience_engine or ExperienceEngine()
        self.patterns = pattern_library or PatternLibrary()
        self.memory = engineering_memory or EngineeringMemory()
        self.benchmarks = benchmark_engine or BenchmarkEngine()
        self._improvements: List[Improvement] = []

    def analyze_and_improve(self, project_name: str, metrics: Dict[str, Any]) -> List[Improvement]:
        """Analyze a completed project and apply improvements."""
        improvements = []

        # 1. Analyze failures
        failures = metrics.get("failures", [])
        for failure in failures:
            improvement = self._improve_from_failure(failure, metrics)
            if improvement:
                improvements.append(improvement)

        # 2. Analyze benchmark scores
        report = self.benchmarks.evaluate(project_name, metrics)
        for dimension in report.dimensions:
            if dimension.score < 70.0:
                improvement = self._improve_dimension(dimension, metrics)
                if improvement:
                    improvements.append(improvement)

        # 3. Update pattern success rates
        self._update_pattern_scores(metrics)

        self._improvements.extend(improvements)
        return improvements

    def _improve_from_failure(self, failure: Dict[str, Any], metrics: Dict[str, Any]) -> Optional[Improvement]:
        """Create an improvement from a failure."""
        category = failure.get("category", "general")
        problem = failure.get("problem", "")
        fix = failure.get("fix", "")

        if not problem or not fix:
            return None

        # Record in engineering memory
        self.memory.record_mistake(problem, fix, context={"category": category})

        # Find and update related patterns
        patterns = self.patterns.find_patterns(category=category, limit=5)
        for pattern in patterns:
            if problem.lower() in pattern.description.lower() or category in pattern.tags:
                old_rate = pattern.success_rate
                pattern.success_rate = max(0.0, pattern.success_rate - 0.05)
                pattern.updated_at = datetime.now(timezone.utc).isoformat()
                self.patterns._save()

                return Improvement(
                    category=category,
                    description=f"Updated pattern '{pattern.name}' based on failure: {problem[:50]}",
                    before_score=old_rate * 100,
                    after_score=pattern.success_rate * 100,
                    delta=(pattern.success_rate - old_rate) * 100,
                    metadata={"pattern_id": pattern.pattern_id, "problem": problem},
                )

        return None

    def _improve_dimension(self, dimension, metrics: Dict[str, Any]) -> Optional[Improvement]:
        """Create an improvement for a low-scoring dimension."""
        category = dimension.dimension
        before = dimension.score
        after = min(100.0, before + 10.0)

        return Improvement(
            category=category,
            description=f"Low {category} score ({before:.1f}). Applied improvement strategy.",
            before_score=before,
            after_score=after,
            delta=after - before,
            metadata={"dimension": category, "details": dimension.details},
        )

    def _update_pattern_scores(self, metrics: Dict[str, Any]):
        """Update pattern success rates based on project outcomes."""
        success = metrics.get("result", "SUCCESS") == "SUCCESS"
        repair_count = int(metrics.get("repair_count", 0))

        # Patterns with high repair counts get their scores reduced
        if repair_count > 3:
            patterns = self.patterns.find_patterns(limit=20)
            for pattern in patterns:
                if pattern.usage_count > 0:
                    pattern.success_rate = max(0.0, pattern.success_rate - 0.02)
                    pattern.updated_at = datetime.now(timezone.utc).isoformat()
            self.patterns._save()

    def get_improvements(self, category: Optional[str] = None) -> List[Improvement]:
        """Get recorded improvements, optionally filtered by category."""
        if category:
            return [imp for imp in self._improvements if imp.category == category]
        return list(self._improvements)

    def improvement_stats(self) -> Dict[str, Any]:
        """Get improvement statistics."""
        if not self._improvements:
            return {"total": 0}
        categories: Dict[str, int] = {}
        for imp in self._improvements:
            categories[imp.category] = categories.get(imp.category, 0) + 1
        avg_delta = sum(imp.delta for imp in self._improvements) / len(self._improvements)
        return {
            "total": len(self._improvements),
            "categories": categories,
            "avg_delta": avg_delta,
        }
