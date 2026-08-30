"""Engineering report generator.

Generates comprehensive engineering reports with scores,
metrics, readiness assessment, and recommendations.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from app.engineering.complexity_estimator import ComplexityEstimate
from app.engineering.pattern_selector import PatternSelection
from app.engineering.risk_analyzer import RiskReport
from app.engineering.technology_selector import TechnologyStack


@dataclass
class EngineeringReport:
    """Complete engineering assessment report."""

    project_name: str
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    requirement_score: float = 0.0
    architecture_score: float = 0.0
    testing_score: float = 0.0
    security_score: float = 0.0
    complexity_score: float = 0.0
    estimated_cost: str = ""
    estimated_time: str = ""
    risk_level: str = "low"  # low, medium, high, critical
    overall_readiness: float = 0.0
    recommendations: List[str] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "project_name": self.project_name,
            "generated_at": self.generated_at,
            "requirement_score": round(self.requirement_score, 1),
            "architecture_score": round(self.architecture_score, 1),
            "testing_score": round(self.testing_score, 1),
            "security_score": round(self.security_score, 1),
            "complexity_score": round(self.complexity_score, 1),
            "estimated_cost": self.estimated_cost,
            "estimated_time": self.estimated_time,
            "risk_level": self.risk_level,
            "overall_readiness": round(self.overall_readiness, 1),
            "recommendations": list(self.recommendations),
            "metrics": dict(self.metrics),
        }


class EngineeringReportGenerator:
    """Generate engineering assessment reports.

    Evaluates requirements, architecture, testing, security,
    and produces actionable recommendations.
    """

    # Score thresholds
    SCORE_THRESHOLDS = {
        "excellent": 90,
        "good": 75,
        "acceptable": 60,
        "needs_work": 40,
    }

    # Cost estimation factors
    COST_FACTORS = {
        "web": {"hourly_rate": 50, "complexity_mult": 1.0},
        "api": {"hourly_rate": 55, "complexity_mult": 1.2},
        "mobile": {"hourly_rate": 60, "complexity_mult": 1.5},
        "desktop": {"hourly_rate": 45, "complexity_mult": 1.0},
        "cli": {"hourly_rate": 40, "complexity_mult": 0.8},
        "library": {"hourly_rate": 50, "complexity_mult": 1.1},
    }

    def generate(self, requirement, analysis, architecture, task_breakdown,
                 resolved_deps, execution_plan, project_state,
                 tech_stack=None, patterns=None, risk_report=None, complexity=None) -> EngineeringReport:
        """Generate complete engineering report.

        Args:
            requirement: Original requirement string.
            analysis: RequirementAnalysis.
            architecture: SystemArchitecture.
            task_breakdown: TaskBreakdown.
            resolved_deps: ResolvedDependencies.
            execution_plan: ExecutionPlan.
            project_state: ProjectState.
            tech_stack: TechnologyStack (optional).
            patterns: List[PatternSelection] (optional).
            risk_report: RiskReport (optional).
            complexity: ComplexityEstimate (optional).

        Returns:
            EngineeringReport with assessment.
        """
        # Calculate scores
        req_score = analysis.confidence * 100
        arch_score = self._score_architecture(architecture)
        test_score = self._score_testing(task_breakdown, project_state)
        sec_score = self._score_security(analysis)
        comp_score = complexity.complexity_score * 10 if complexity else self._score_complexity(task_breakdown, resolved_deps)

        # Use provided tech stack or defaults
        if tech_stack is None:
            tech_stack = TechnologyStack()

        # Use provided risk or calculate
        if risk_report is None:
            risk_report = RiskReport(project_name=analysis.project_name or "Unknown")

        # Estimate cost and time
        total_hours = task_breakdown.total_estimated_hours
        if complexity and complexity.estimated_hours:
            total_hours = complexity.estimated_hours
        cost_data = self._estimate_cost(total_hours, analysis.project_type)
        time_str = self._estimate_time(total_hours)

        # Overall readiness
        weights = {"req": 0.2, "arch": 0.2, "test": 0.15, "sec": 0.15, "comp": 0.15, "tech": 0.15}
        readiness = (
            weights["req"] * req_score +
            weights["arch"] * arch_score +
            weights["test"] * test_score +
            weights["sec"] * sec_score +
            weights["comp"] * comp_score +
            weights["tech"] * 85  # Tech selection baseline
        )

        # Recommendations
        recommendations = self._generate_recommendations(
            analysis, architecture, test_score, sec_score, comp_score, resolved_deps, project_state
        )

        # Metrics
        metrics = {
            "total_tasks": task_breakdown.total_tasks,
            "total_phases": execution_plan.total_phases,
            "estimated_hours": round(total_hours, 1),
            "parallel_groups": len(resolved_deps.parallel_groups),
            "has_cycles": resolved_deps.has_cycles,
            "current_progress": project_state.status,
        }

        return EngineeringReport(
            project_name=requirement[:50],
            requirement_score=req_score,
            architecture_score=arch_score,
            testing_score=test_score,
            security_score=sec_score,
            complexity_score=comp_score,
            estimated_cost=cost_data,
            estimated_time=time_str,
            risk_level=risk_report.overall_risk_level if risk_report else "low",
            overall_readiness=readiness,
            recommendations=recommendations,
            metrics=metrics,
        )

    def _score_architecture(self, architecture) -> float:
        """Score architecture design 0-100."""
        score = 70.0
        if len(architecture.components) >= 5:
            score += 10
        if architecture.tech_stack.get("backend"):
            score += 5
        if architecture.tech_stack.get("database"):
            score += 5
        if architecture.tech_stack.get("cache"):
            score += 5
        if architecture.tech_stack.get("monitoring"):
            score += 5
        return min(100.0, score)

    def _score_testing(self, task_breakdown, project_state) -> float:
        """Score testing plan 0-100."""
        test_tasks = [t for t in task_breakdown.tasks if t.category == "testing"]
        if not test_tasks:
            return 30.0
        score = 50.0 + len(test_tasks) * 10
        if project_state.test_coverage > 0:
            score += project_state.test_coverage * 0.5
        return min(100.0, score)

    def _score_security(self, analysis) -> float:
        """Score security considerations 0-100."""
        score = 60.0
        if "authentication" not in analysis.missing_information:
            score += 15
        if "security" not in analysis.missing_information:
            score += 15
        if "deployment" not in analysis.missing_information:
            score += 10
        return min(100.0, score)

    def _score_complexity(self, task_breakdown, resolved_deps) -> float:
        """Score project complexity 0-100 (lower is better)."""
        base_complexity = min(100, task_breakdown.total_tasks * 2)
        if resolved_deps.has_cycles:
            base_complexity += 20
        if len(resolved_deps.parallel_groups) > 3:
            base_complexity -= 10
        return max(0, min(100, base_complexity))

    def _estimate_cost(self, hours: float, project_type: str) -> str:
        """Estimate project cost."""
        factor = self.COST_FACTORS.get(project_type, self.COST_FACTORS["web"])
        hourly_rate = factor["hourly_rate"]
        complexity_mult = factor["complexity_mult"]
        total_cost = hours * hourly_rate * complexity_mult
        return f"${total_cost:,.0f}"

    def _estimate_time(self, hours: float) -> str:
        """Estimate project completion time."""
        days = hours / 8  # 8 hour workdays
        weeks = days / 5  # 5 day weeks
        if weeks < 1:
            return f"{days:.1f} days"
        elif weeks < 4:
            return f"{weeks:.1f} weeks"
        else:
            months = weeks / 4
            return f"{months:.1f} months"

    def _assess_risk(self, analysis, architecture, resolved_deps) -> str:
        """Assess project risk level."""
        risk_score = 0
        if resolved_deps.has_cycles:
            risk_score += 3
        if len(analysis.missing_information) > 4:
            risk_score += 2
        if architecture.tech_stack.get("database") in ("MongoDB", "Cassandra"):
            risk_score += 1
        if risk_score >= 4:
            return "critical"
        elif risk_score >= 3:
            return "high"
        elif risk_score >= 2:
            return "medium"
        else:
            return "low"

    def _generate_recommendations(self, analysis, architecture, test_score,
                                  sec_score, comp_score, resolved_deps, project_state) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        if analysis.confidence < 0.6:
            recommendations.append("Requirements need clarification before proceeding")

        if test_score < 60:
            recommendations.append("Increase test coverage - target > 80%")

        if sec_score < 70:
            recommendations.append("Add security layer: authentication, authorization, encryption")

        if comp_score > 70:
            recommendations.append("Consider breaking down complex tasks for better maintainability")

        if resolved_deps.has_cycles:
            recommendations.append("Resolve circular dependencies in architecture")

        if not architecture.tech_stack.get("cache"):
            recommendations.append("Add caching layer for performance")

        if not architecture.tech_stack.get("monitoring"):
            recommendations.append("Add monitoring and logging infrastructure")

        if project_state.runtime_errors:
            recommendations.append(f"Address {len(project_state.runtime_errors)} runtime errors")

        if not recommendations:
            recommendations.append("Project looks good to proceed")

        return recommendations
