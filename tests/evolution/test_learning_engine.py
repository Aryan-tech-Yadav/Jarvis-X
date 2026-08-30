"""Unit tests for Autonomous Learning Engine."""

import tempfile
import unittest
from pathlib import Path

from app.evolution.learning_engine import AutonomousLearningEngine


class TestLearningEngine(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.knowledge_dir = Path(self.temp_dir.name) / "knowledge"
        self.engine = AutonomousLearningEngine(str(self.knowledge_dir))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_process_project_completion_and_evolution_score(self):
        res = self.engine.process_project_completion(
            project_name="Hospital ERP",
            execution_time_sec=120.0,
            planning_score=96.0,
            execution_score=94.0,
            quality_score=95.0,
            repair_count=1,
            test_coverage=92.0,
            result="SUCCESS",
            domain="healthcare",
            architecture="FastAPI + PostgreSQL",
            stack=["fastapi", "postgresql", "redis"],
            failures_encountered=[
                {
                    "problem": "Missing Configuration",
                    "reason": "Missing DB_PORT in env",
                    "root_cause": "KeyError in settings",
                    "fix_strategy": "Added fallback port 5432",
                    "category": "configuration",
                    "success": True,
                }
            ],
            lessons=["Always initialize default PostgreSQL port to 5432"],
        )

        self.assertIn("experience", res)
        self.assertIn("evolution_score", res)
        self.assertGreaterEqual(res["evolution_score"]["overall_evolution_score"], 90.0)
        self.assertGreaterEqual(len(res["recommendations"]), 1)

    def test_evolution_dashboard_and_weekly_review(self):
        # Process 2 projects
        self.engine.process_project_completion("CRM App", 80.0, 95.0, 93.0, 94.0, domain="crm")
        self.engine.process_project_completion("Inventory System", 90.0, 96.0, 94.0, 95.0, domain="inventory")

        dashboard = self.engine.get_evolution_dashboard()
        self.assertEqual(dashboard["status"], "🟢 Healthy")
        self.assertEqual(dashboard["widgets"]["experience"]["total_projects"], 2)
        self.assertIn("evolution_score", dashboard["widgets"])

        review = self.engine.generate_weekly_review()
        self.assertGreaterEqual(review.total_projects, 2)
        md = review.to_markdown()
        self.assertIn("Jarvis-X Weekly Autonomous Self-Review", md)
