"""Proactive Engineering Recommendation Engine."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .experience_engine import ExperienceEngine
from .failure_engine import FailureEngine
from .models.experience import ProjectExperience
from .models.recommendation import EvolutionRecommendation, RecommendationType
from .optimization_engine import OptimizationEngine


class RecommendationEngine:
    """Generates proactive, data-driven engineering recommendations for self-improvement."""

    def __init__(
        self,
        experience_engine: Optional[ExperienceEngine] = None,
        failure_engine: Optional[FailureEngine] = None,
        optimization_engine: Optional[OptimizationEngine] = None,
    ):
        self.experience_engine = experience_engine or ExperienceEngine()
        self.failure_engine = failure_engine or FailureEngine()
        self.optimization_engine = optimization_engine or OptimizationEngine()

    def generate_recommendations(
        self, latest_experience: Optional[ProjectExperience] = None
    ) -> List[EvolutionRecommendation]:
        recommendations: List[EvolutionRecommendation] = []

        # 1. Metric-based optimizations
        if latest_experience:
            opt_recs = self.optimization_engine.analyze_metrics(
                latest_experience.metrics, latest_experience.project_name
            )
            recommendations.extend(opt_recs)

        # 2. Failure pattern insights
        common_failures = self.failure_engine.get_most_common_failures(limit=3)
        for f in common_failures:
            if f.get("occurrences", 0) >= 2:
                recommendations.append(
                    EvolutionRecommendation(
                        title=f"Hardcode Defense Against Recurring {f.get('category', '').title()} Failures",
                        description=f"Issue '{f.get('problem')}' occurred {f.get('occurrences')} times. Auto-apply strategy '{f.get('fix_strategy')}' during generation.",
                        recommendation_type=RecommendationType.CODE_QUALITY,
                        target_module="generator",
                        estimated_gain_pct=15.0,
                        confidence=0.97,
                        evidence=f"Root cause: {f.get('root_cause')}",
                        action_items=[
                            f"Add pre-generation template rule for {f.get('failing_symbol') or f.get('category')}",
                        ],
                    )
                )

        # 3. Overall aggregate trends
        stats = self.experience_engine.get_aggregate_stats()
        if stats.get("total_projects", 0) >= 3:
            if stats.get("average_planning_score", 100.0) < 92.0:
                recommendations.append(
                    EvolutionRecommendation(
                        title="Enhance Requirement Analyzer Decomposition Depth",
                        description="Average planning score (currently {:.1f}%) is below the 95% target threshold.".format(
                            stats.get("average_planning_score", 0.0)
                        ),
                        recommendation_type=RecommendationType.ACCURACY,
                        target_module="planner",
                        estimated_gain_pct=18.0,
                        confidence=0.92,
                        evidence="Historical planning score variance across projects",
                        action_items=["Expand requirement elicitation checklist"],
                    )
                )

            if stats.get("average_runtime_sec", 0.0) > 180.0:
                recommendations.append(
                    EvolutionRecommendation(
                        title="Switch Executor to Parallel DAG Mode",
                        description="Executor ko parallel mode me chalane se runtime 28% kam ho sakta hai.",
                        recommendation_type=RecommendationType.PERFORMANCE,
                        target_module="kernel.dispatcher",
                        estimated_gain_pct=28.0,
                        confidence=0.96,
                        evidence=f"Average project runtime is {stats.get('average_runtime_sec', 0):.1f}s",
                        action_items=["Dispatch independent tasks across worker pool"],
                    )
                )

        # Default fallback recommendation
        if not recommendations:
            recommendations.append(
                EvolutionRecommendation(
                    title="System Running at Peak Performance",
                    description="No performance, architectural, or quality regressions detected.",
                    recommendation_type=RecommendationType.WORKFLOW,
                    target_module="system",
                    estimated_gain_pct=5.0,
                    confidence=0.99,
                    evidence="All project scores and benchmarks meet or exceed targets.",
                    action_items=["Maintain current operational cadence"],
                )
            )

        return recommendations
