"""Unit tests for Optimization and Recommendation Engines."""

import unittest

from app.evolution.models.experience import ExecutionMetrics, ProjectExperience
from app.evolution.optimization_engine import OptimizationEngine
from app.evolution.recommendation_engine import RecommendationEngine


class TestOptimizationAndRecommendation(unittest.TestCase):
    def test_optimization_detects_slow_planning_and_execution(self):
        opt = OptimizationEngine()
        metrics = ExecutionMetrics(
            planning_time_sec=45.0,
            coding_time_sec=150.0,
            test_time_sec=70.0,
            repair_time_sec=80.0,
            total_time_sec=345.0,
            memory_peak_mb=650.0,
        )

        recs = opt.analyze_metrics(metrics, "Heavy ERP")
        self.assertGreaterEqual(len(recs), 3)

        titles = [r.title for r in recs]
        self.assertTrue(any("Parallel" in t for t in titles))
        self.assertTrue(any("Memory" in t for t in titles))
        self.assertTrue(any("Planner" in t for t in titles))

    def test_recommendation_engine_generates_proactive_advice(self):
        rec_engine = RecommendationEngine()
        exp = ProjectExperience(
            project_name="TestApp",
            metrics=ExecutionMetrics(
                planning_time_sec=60.0,
                coding_time_sec=100.0,
                total_time_sec=180.0,
            ),
        )
        recs = rec_engine.generate_recommendations(exp)
        self.assertGreaterEqual(len(recs), 1)
        self.assertGreater(recs[0].estimated_gain_pct, 0.0)
