"""Brain Analytics - Daily intelligence reports.

Bonus: Brain Analytics
Har din Jarvis khud report banaye:

Today's Tasks: 43
Planning Accuracy: 94%
Average Confidence: 91%
Auto-Recovered Errors: 17
New Rules Learned: 6
Repeated Mistakes: 2
Most Used Strategy: Deep Reasoning
Weakest Skill: Dependency Resolution
Recommendation: Improve dependency analysis module.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.logger import Logger


@dataclass
class DailyReport:
    """Daily brain analytics report."""
    date: str
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    planning_accuracy: float = 0.0
    average_confidence: float = 0.0
    auto_recovered_errors: int = 0
    new_rules_learned: int = 0
    repeated_mistakes: int = 0
    most_used_strategy: str = ""
    weakest_skill: str = ""
    recommendations: List[str] = field(default_factory=list)
    skill_scores: Dict[str, float] = field(default_factory=dict)


class BrainAnalytics:
    """Generate daily intelligence reports.

    Tracks:
      - Task completion rates
      - Planning accuracy
      - Confidence levels
      - Error recovery
      - Learning progress
      - Strategy usage
      - Skill weaknesses
    """

    def __init__(self, analytics_dir: str = "data/analytics"):
        self.analytics_dir = Path(analytics_dir)
        self.analytics_dir.mkdir(parents=True, exist_ok=True)
        self._daily_reports: List[DailyReport] = []
        self._task_history: List[Dict[str, Any]] = []

    def record_task(self, task_result: Dict[str, Any]):
        """Record task for analytics.

        Args:
            task_result: Task execution result
        """
        self._task_history.append(task_result)

        # Generate daily report if needed
        today = datetime.now().strftime("%Y-%m-%d")
        if not self._daily_reports or self._daily_reports[-1].date != today:
            self._generate_daily_report()

    def _generate_daily_report(self) -> DailyReport:
        """Generate daily analytics report."""
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        # Filter today's tasks
        today_tasks = [
            t for t in self._task_history
            if datetime.fromisoformat(t.get("timestamp", "")).strftime("%Y-%m-%d") == today
        ]

        report = DailyReport(date=today)
        report.total_tasks = len(today_tasks)
        report.successful_tasks = sum(1 for t in today_tasks if t.get("success"))
        report.failed_tasks = report.total_tasks - report.successful_tasks

        # Calculate metrics
        if today_tasks:
            confidences = [t.get("confidence", 0.0) for t in today_tasks if t.get("confidence")]
            report.average_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            quality_scores = [t.get("quality_score", 0.0) for t in today_tasks]
            report.planning_accuracy = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0

            report.auto_recovered_errors = sum(t.get("metrics", {}).get("errors_fixed", 0) for t in today_tasks)

        # Analyze strategies
        strategies: Dict[str, int] = {}
        for task in today_tasks:
            strategy = task.get("strategy", "unknown")
            strategies[strategy] = strategies.get(strategy, 0) + 1

        if strategies:
            report.most_used_strategy = max(strategies, key=strategies.get)

        # Identify weakest skill
        skill_scores: Dict[str, List[float]] = {}
        for task in today_tasks:
            skill = task.get("skill", "general")
            score = task.get("quality_score", 0.0)
            if skill not in skill_scores:
                skill_scores[skill] = []
            skill_scores[skill].append(score)

        if skill_scores:
            avg_scores = {skill: sum(scores)/len(scores) for skill, scores in skill_scores.items()}
            report.weakest_skill = min(avg_scores, key=avg_scores.get)
            report.skill_scores = avg_scores

        # Generate recommendations
        report.recommendations = self._generate_recommendations(report)

        # Save report
        self._save_report(report)
        self._daily_reports.append(report)

        return report

    def _generate_recommendations(self, report: DailyReport) -> List[str]:
        """Generate recommendations based on report."""
        recommendations = []

        if report.planning_accuracy < 80.0:
            recommendations.append("Improve planning accuracy through better decomposition")

        if report.auto_recovered_errors > 5:
            recommendations.append("Reduce initial errors through pre-validation")

        if report.failed_tasks > report.total_tasks * 0.2:
            recommendations.append("Investigate failure patterns")

        if report.weakest_skill:
            recommendations.append(f"Improve weakest skill: {report.weakest_skill}")

        if not recommendations:
            recommendations.append("Continue current approach")

        return recommendations

    def _save_report(self, report: DailyReport):
        """Save daily report."""
        try:
            filepath = self.analytics_dir / f"report_{report.date}.json"
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump({
                    "date": report.date,
                    "total_tasks": report.total_tasks,
                    "successful_tasks": report.successful_tasks,
                    "failed_tasks": report.failed_tasks,
                    "planning_accuracy": report.planning_accuracy,
                    "average_confidence": report.average_confidence,
                    "auto_recovered_errors": report.auto_recovered_errors,
                    "new_rules_learned": report.new_rules_learned,
                    "repeated_mistakes": report.repeated_mistakes,
                    "most_used_strategy": report.most_used_strategy,
                    "weakest_skill": report.weakest_skill,
                    "recommendations": report.recommendations,
                    "skill_scores": report.skill_scores,
                }, f, indent=2)
        except Exception as exc:
            Logger.warning(f"[Analytics] Save failed: {exc}")

    def get_latest_report(self) -> Optional[DailyReport]:
        """Get latest daily report."""
        return self._daily_reports[-1] if self._daily_reports else None

    def get_report_summary(self) -> str:
        """Get text summary of latest report."""
        report = self.get_latest_report()
        if not report:
            return "No analytics data available"

        lines = [
            f"Date: {report.date}",
            f"Today's Tasks: {report.total_tasks}",
            f"Successful: {report.successful_tasks}",
            f"Failed: {report.failed_tasks}",
            f"Planning Accuracy: {report.planning_accuracy:.1f}%",
            f"Average Confidence: {report.average_confidence:.1f}%",
            f"Auto-Recovered Errors: {report.auto_recovered_errors}",
            f"New Rules Learned: {report.new_rules_learned}",
            f"Most Used Strategy: {report.most_used_strategy}",
            f"Weakest Skill: {report.weakest_skill}",
            "",
            "Recommendations:",
        ]

        for rec in report.recommendations:
            lines.append(f"  - {rec}")

        return "\n".join(lines)
