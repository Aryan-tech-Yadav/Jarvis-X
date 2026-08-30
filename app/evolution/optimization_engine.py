"""Autonomous Optimization Engine for analyzing metrics, detecting bottlenecks, and proposing gains."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .models.experience import ExecutionMetrics, ProjectExperience
from .models.recommendation import EvolutionRecommendation, RecommendationType


class OptimizationEngine:
    """Detects inefficiencies across planning, execution, memory, and token usage."""

    def analyze_metrics(
        self, metrics: ExecutionMetrics, project_name: str = "Project"
    ) -> List[EvolutionRecommendation]:
        recommendations: List[EvolutionRecommendation] = []

        # 1. Slow Planning Check (planning > 30% of total runtime)
        if metrics.total_time_sec > 0 and (metrics.planning_time_sec / metrics.total_time_sec) > 0.30:
            gain = min(40.0, ((metrics.planning_time_sec / metrics.total_time_sec) - 0.20) * 100.0)
            recommendations.append(
                EvolutionRecommendation(
                    title="Optimize Planner Graph Decomposition",
                    description=f"Planning consumed {(metrics.planning_time_sec / metrics.total_time_sec)*100:.1f}% of total execution time in {project_name}.",
                    recommendation_type=RecommendationType.PERFORMANCE,
                    target_module="planner",
                    estimated_gain_pct=round(gain, 1),
                    confidence=0.94,
                    evidence=f"Planning time: {metrics.planning_time_sec:.2f}s, Total time: {metrics.total_time_sec:.2f}s",
                    action_items=[
                        "Enable hierarchical sub-task caching",
                        "Use AST-based fast requirement summarization",
                    ],
                )
            )

        # 2. Slow Execution / Serial Execution
        if metrics.coding_time_sec > 120.0 or metrics.test_time_sec > 60.0:
            recommendations.append(
                EvolutionRecommendation(
                    title="Enable Parallel Node Execution in Kernel",
                    description="Independent task execution executed serially, slowing overall build time.",
                    recommendation_type=RecommendationType.PERFORMANCE,
                    target_module="kernel.scheduler",
                    estimated_gain_pct=32.0,
                    confidence=0.96,
                    evidence=f"Coding time ({metrics.coding_time_sec:.1f}s) and Test time ({metrics.test_time_sec:.1f}s) can run concurrently across DAG levels.",
                    action_items=[
                        "Set Kernel max_parallel >= 4",
                        "Schedule non-dependent test suites concurrently",
                    ],
                )
            )

        # 3. High Memory Usage
        if metrics.memory_peak_mb > 500.0:
            recommendations.append(
                EvolutionRecommendation(
                    title="Reduce Memory Footprint via Generator Streaming",
                    description=f"Peak RAM reached {metrics.memory_peak_mb:.1f}MB during execution.",
                    recommendation_type=RecommendationType.PERFORMANCE,
                    target_module="runtime",
                    estimated_gain_pct=25.0,
                    confidence=0.91,
                    evidence=f"Peak memory: {metrics.memory_peak_mb:.1f}MB exceeds 500MB threshold.",
                    action_items=[
                        "Stream AST file reads in chunks",
                        "Run garbage collection explicitly after test suite runs",
                    ],
                )
            )

        # 4. Excessive Repair Loops
        if metrics.repair_time_sec > metrics.coding_time_sec * 0.5 and metrics.repair_time_sec > 10.0:
            recommendations.append(
                EvolutionRecommendation(
                    title="Pre-Flight Code Linting Before Test Generation",
                    description="Frequent self-repair cycles observed for syntax and basic import errors.",
                    recommendation_type=RecommendationType.WORKFLOW,
                    target_module="repair_engine",
                    estimated_gain_pct=20.0,
                    confidence=0.95,
                    evidence=f"Repair time: {metrics.repair_time_sec:.1f}s is {metrics.repair_time_sec/max(1.0, metrics.coding_time_sec)*100:.1f}% of coding time.",
                    action_items=[
                        "Insert AST syntax check in executor before running full test suite",
                        "Auto-inject standard imports during code generation",
                    ],
                )
            )

        return recommendations
