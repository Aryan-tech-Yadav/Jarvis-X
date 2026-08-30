"""Reflection Engine - Post-task analysis and learning.

Week 5: Reflection Engine
Task complete hone ke baad:
  What went well?
  What failed?
  Could another plan be better?
  Should memory update?
  Should rules update?
  Should benchmark run?

Reflection mandatory.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.logger import Logger


@dataclass
class ReflectionInsight:
    """Single insight from reflection."""
    insight_id: str
    category: str  # success, failure, improvement, learning
    description: str
    severity: str = "medium"  # low, medium, high
    action_required: bool = False
    suggested_action: str = ""
    confidence: float = 1.0


@dataclass
class ReflectionReport:
    """Complete reflection report."""
    task_id: str
    timestamp: str
    what_went_well: List[str] = field(default_factory=list)
    what_failed: List[str] = field(default_factory=list)
    could_improve: List[str] = field(default_factory=list)
    insights: List[ReflectionInsight] = field(default_factory=list)
    should_update_memory: bool = False
    should_update_rules: bool = False
    should_run_benchmark: bool = False
    overall_rating: float = 0.0
    duration: float = 0.0


class ReflectionEngine:
    """Mandatory post-task reflection.

    Every task must go through reflection before completion.
    """

    def __init__(self, reflections_dir: str = "data/reflections", event_bus=None):
        self.reflections_dir = Path(reflections_dir)
        self.reflections_dir.mkdir(parents=True, exist_ok=True)
        self.event_bus = event_bus
        self._reflection_history: List[ReflectionReport] = []

    def reflect(self, task_result: Dict[str, Any], context: Dict[str, Any] = None) -> ReflectionReport:
        """Perform reflection on completed task.

        Args:
            task_result: Task execution result
            context: Task context

        Returns:
            ReflectionReport with insights
        """
        start_time = time.perf_counter()
        context = context or {}

        task_id = task_result.get("task_id", f"task_{int(time.time())}")
        success = task_result.get("success", False)
        quality_score = task_result.get("quality_score", 0.0)
        errors = task_result.get("errors", [])
        metrics = task_result.get("metrics", {})

        report = ReflectionReport(
            task_id=task_id,
            timestamp=datetime.now().isoformat(),
        )

        # Analyze what went well
        report.what_went_well = self._analyze_went_well(task_result, context)

        # Analyze what failed
        report.what_failed = self._analyze_failures(task_result, context)

        # Identify improvements
        report.could_improve = self._identify_improvements(task_result, context)

        # Generate insights
        report.insights = self._generate_insights(task_result, context, report)

        # Determine actions
        report.should_update_memory = self._should_update_memory(task_result, report)
        report.should_update_rules = self._should_update_rules(task_result, report)
        report.should_run_benchmark = self._should_run_benchmark(task_result, report)

        # Overall rating
        report.overall_rating = self._calculate_rating(task_result, report)

        duration = time.perf_counter() - start_time
        report.duration = duration

        # Save reflection
        self._save_reflection(report)

        self._reflection_history.append(report)
        self._emit("REFLECTION_COMPLETED", {
            "task_id": task_id,
            "rating": report.overall_rating,
            "insights": len(report.insights),
        })

        return report

    def _analyze_went_well(self, task_result: Dict[str, Any], context: Dict[str, Any]) -> List[str]:
        """Analyze what went well."""
        went_well = []

        if task_result.get("success"):
            went_well.append("Task completed successfully")

        quality_score = task_result.get("quality_score", 0.0)
        if quality_score >= 90.0:
            went_well.append(f"High quality output ({quality_score:.0f}%)")

        metrics = task_result.get("metrics", {})
        if metrics.get("errors_fixed", 0) > 0:
            went_well.append(f"Auto-recovered {metrics['errors_fixed']} errors")

        if metrics.get("tests_passed", 0) > 0:
            went_well.append(f"Tests passing ({metrics['tests_passed']})")

        duration = metrics.get("duration_seconds", 0.0)
        if duration < 60:
            went_well.append("Fast execution")

        if not went_well:
            went_well.append("Task completed")

        return went_well

    def _analyze_failures(self, task_result: Dict[str, Any], context: Dict[str, Any]) -> List[str]:
        """Analyze what failed."""
        failures = []

        if not task_result.get("success"):
            failures.append("Task failed to complete")

        errors = task_result.get("errors", [])
        if errors:
            failures.extend(errors[:5])

        quality_score = task_result.get("quality_score", 0.0)
        if quality_score < 70.0:
            failures.append(f"Low quality output ({quality_score:.0f}%)")

        metrics = task_result.get("metrics", {})
        if metrics.get("tests_failed", 0) > 0:
            failures.append(f"Test failures: {metrics['tests_failed']}")

        return failures

    def _identify_improvements(self, task_result: Dict[str, Any], context: Dict[str, Any]) -> List[str]:
        """Identify potential improvements."""
        improvements = []

        quality_score = task_result.get("quality_score", 0.0)
        if quality_score < 80.0:
            improvements.append("Improve code generation quality")

        metrics = task_result.get("metrics", {})
        if metrics.get("errors_fixed", 0) > 3:
            improvements.append("Reduce initial errors through better planning")

        if metrics.get("tests_failed", 0) > 0:
            improvements.append("Add more comprehensive testing")

        if not improvements:
            improvements.append("Continue current approach")

        return improvements

    def _generate_insights(self, task_result: Dict[str, Any], context: Dict[str, Any], report: ReflectionReport) -> List[ReflectionInsight]:
        """Generate insights from reflection."""
        insights = []

        # Success insight
        if task_result.get("success"):
            insights.append(ReflectionInsight(
                insight_id=f"ins_{int(time.time())}_1",
                category="success",
                description="Task completed successfully",
                severity="low",
                action_required=False,
            ))

        # Quality insight
        quality_score = task_result.get("quality_score", 0.0)
        if quality_score < 80.0:
            insights.append(ReflectionInsight(
                insight_id=f"ins_{int(time.time())}_2",
                category="improvement",
                description=f"Quality score {quality_score:.0f}% below target",
                severity="high",
                action_required=True,
                suggested_action="Review code generation pipeline",
            ))

        # Error pattern insight
        errors = task_result.get("errors", [])
        if len(errors) > 3:
            insights.append(ReflectionInsight(
                insight_id=f"ins_{int(time.time())}_3",
                category="failure",
                description=f"Recurring errors detected: {len(errors)} errors",
                severity="medium",
                action_required=True,
                suggested_action="Update error prevention rules",
            ))

        return insights

    def _should_update_memory(self, task_result: Dict[str, Any], report: ReflectionReport) -> bool:
        """Determine if memory should be updated."""
        return (
            task_result.get("success")
            and task_result.get("quality_score", 0.0) >= 80.0
        ) or len(report.insights) > 3

    def _should_update_rules(self, task_result: Dict[str, Any], report: ReflectionReport) -> bool:
        """Determine if rules should be updated."""
        return (
            task_result.get("quality_score", 0.0) < 70.0
            or len(report.what_failed) > 2
        )

    def _should_run_benchmark(self, task_result: Dict[str, Any], report: ReflectionReport) -> bool:
        """Determine if benchmark should run."""
        return task_result.get("success") and task_result.get("quality_score", 0.0) >= 90.0

    def _calculate_rating(self, task_result: Dict[str, Any], report: ReflectionReport) -> float:
        """Calculate overall rating."""
        success_score = 100.0 if task_result.get("success") else 0.0
        quality_score = task_result.get("quality_score", 0.0)
        efficiency_score = max(0.0, 100.0 - (task_result.get("metrics", {}).get("duration_seconds", 0.0) / 5.0))

        return (success_score * 0.4 + quality_score * 0.4 + efficiency_score * 0.2)

    def _save_reflection(self, report: ReflectionReport):
        """Save reflection to disk."""
        try:
            filename = f"reflection_{report.task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.reflections_dir / filename
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump({
                    "task_id": report.task_id,
                    "timestamp": report.timestamp,
                    "what_went_well": report.what_went_well,
                    "what_failed": report.what_failed,
                    "could_improve": report.could_improve,
                    "insights": [
                        {
                            "category": i.category,
                            "description": i.description,
                            "severity": i.severity,
                            "action_required": i.action_required,
                            "suggested_action": i.suggested_action,
                        }
                        for i in report.insights
                    ],
                    "should_update_memory": report.should_update_memory,
                    "should_update_rules": report.should_update_rules,
                    "should_run_benchmark": report.should_run_benchmark,
                    "overall_rating": report.overall_rating,
                    "duration": report.duration,
                }, f, indent=2)
        except Exception as exc:
            Logger.warning(f"[Reflection] Save failed: {exc}")

    def _emit(self, event_type: str, payload: Dict[str, Any]):
        """Emit event through event bus."""
        if self.event_bus:
            try:
                self.event_bus.publish(event_type, payload)
            except Exception:
                pass

    def get_reflection_stats(self) -> Dict[str, Any]:
        """Get reflection statistics."""
        if not self._reflection_history:
            return {"total_reflections": 0}

        ratings = [r.overall_rating for r in self._reflection_history]
        return {
            "total_reflections": len(self._reflection_history),
            "average_rating": sum(ratings) / len(ratings),
            "latest_rating": ratings[-1] if ratings else 0,
        }
