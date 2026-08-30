"""Reflection Engine - Automatic post-execution analysis.

Analyzes completed tasks to identify:
  - What went well
  - Mistakes made
  - Repair count
  - Time taken
  - Failure reasons
  - Improvement suggestions
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.logger import Logger


@dataclass
class ReflectionResult:
    """Result of task reflection."""
    task_id: str
    project_name: str
    timestamp: str
    went_well: List[str] = field(default_factory=list)
    mistakes: List[str] = field(default_factory=list)
    repairs_count: int = 0
    time_taken_seconds: float = 0.0
    failure_reasons: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    quality_score: float = 0.0
    metrics: Dict[str, Any] = field(default_factory=dict)


class ReflectionEngine:
    """Automatic reflection engine for post-task analysis.

    Generates insights from task execution to improve future performance.
    """

    def __init__(self, reflections_dir: str = "data/reflections"):
        self.reflections_dir = Path(reflections_dir)
        self.reflections_dir.mkdir(parents=True, exist_ok=True)

    def reflect(self, context: Any) -> ReflectionResult:
        """Perform reflection on completed task.

        Args:
            context: Runtime context or task result

        Returns:
            ReflectionResult with analysis
        """
        task_id = getattr(context, 'session_id', 'unknown')
        project_name = getattr(context.project, 'project_name', 'unknown') if hasattr(context, 'project') else 'unknown'
        metrics = getattr(context, 'metrics', None)

        result = ReflectionResult(
            task_id=task_id,
            project_name=project_name,
            timestamp=datetime.now().isoformat(),
        )

        # Analyze metrics
        if metrics:
            result.time_taken_seconds = getattr(metrics, 'duration_seconds', 0.0)
            result.repairs_count = getattr(metrics, 'errors_fixed', 0)
            result.quality_score = getattr(metrics, 'quality_score', 0.0)
            result.metrics = {
                'files_generated': getattr(metrics, 'files_generated', 0),
                'tests_passed': getattr(metrics, 'tests_passed', 0),
                'tests_failed': getattr(metrics, 'tests_failed', 0),
                'errors_fixed': getattr(metrics, 'errors_fixed', 0),
            }

        # Analyze what went well
        result.went_well = self._analyze_went_well(context, result)

        # Analyze mistakes
        result.mistakes = self._analyze_mistakes(context, result)

        # Analyze failures
        result.failure_reasons = self._analyze_failures(context, result)

        # Generate suggestions
        result.suggestions = self._generate_suggestions(result)

        # Save reflection
        self._save_reflection(result)

        Logger.info(f"[Reflection] Completed for {project_name}: {result.quality_score:.1f}% quality, {result.repairs_count} repairs")
        return result

    def _analyze_went_well(self, context: Any, result: ReflectionResult) -> List[str]:
        """Analyze what went well."""
        went_well = []

        if result.quality_score >= 90.0:
            went_well.append("High quality output achieved")

        if result.repairs_count == 0:
            went_well.append("No repairs needed - clean execution")

        if result.time_taken_seconds < 60:
            went_well.append("Fast execution time")

        if result.metrics.get('tests_passed', 0) > 0:
            went_well.append(f"Tests passing ({result.metrics['tests_passed']})")

        if not went_well:
            went_well.append("Task completed successfully")

        return went_well

    def _analyze_mistakes(self, context: Any, result: ReflectionResult) -> List[str]:
        """Analyze mistakes made."""
        mistakes = []

        if result.repairs_count > 5:
            mistakes.append(f"High repair count: {result.repairs_count}")

        if result.quality_score < 70.0:
            mistakes.append("Low quality output")

        if result.time_taken_seconds > 300:
            mistakes.append("Execution took too long")

        if result.metrics.get('tests_failed', 0) > 5:
            mistakes.append(f"Many test failures: {result.metrics['tests_failed']}")

        return mistakes

    def _analyze_failures(self, context: Any, result: ReflectionResult) -> List[str]:
        """Analyze failure reasons."""
        failures = []

        if hasattr(context, 'errors') and context.errors:
            failures.extend(context.errors[:5])

        if result.quality_score < 50.0:
            failures.append("Quality score critically low")

        return failures

    def _generate_suggestions(self, result: ReflectionResult) -> List[str]:
        """Generate improvement suggestions."""
        suggestions = []

        if result.repairs_count > 3:
            suggestions.append("Improve initial code generation quality")

        if result.quality_score < 80.0:
            suggestions.append("Add more comprehensive testing")

        if result.time_taken_seconds > 120:
            suggestions.append("Optimize execution pipeline")

        if result.metrics.get('tests_failed', 0) > 0:
            suggestions.append("Fix failing tests before finalizing")

        if not suggestions:
            suggestions.append("Continue current approach")

        return suggestions

    def _save_reflection(self, result: ReflectionResult):
        """Save reflection to disk."""
        try:
            filename = f"reflection_{result.task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.reflections_dir / filename
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump({
                    "task_id": result.task_id,
                    "project_name": result.project_name,
                    "timestamp": result.timestamp,
                    "went_well": result.went_well,
                    "mistakes": result.mistakes,
                    "repairs_count": result.repairs_count,
                    "time_taken_seconds": result.time_taken_seconds,
                    "failure_reasons": result.failure_reasons,
                    "suggestions": result.suggestions,
                    "quality_score": result.quality_score,
                    "metrics": result.metrics,
                }, f, indent=2)
        except Exception as exc:
            Logger.warning(f"[Reflection] Save failed: {exc}")

    def get_reflection_history(self, project_name: str = "") -> List[Dict[str, Any]]:
        """Get reflection history.

        Args:
            project_name: Filter by project name

        Returns:
            List of reflection records
        """
        reflections = []
        for filepath in self.reflections_dir.glob("*.json"):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if not project_name or data.get("project_name") == project_name:
                        reflections.append(data)
            except Exception:
                pass
        return sorted(reflections, key=lambda x: x.get("timestamp", ""), reverse=True)
