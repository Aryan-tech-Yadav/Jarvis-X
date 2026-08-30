"""Unit tests for Showcase, Demos, Scorecard, and Omega Benchmark Certification."""

import tempfile
import unittest
from pathlib import Path

from app.evolution.learning_engine import AutonomousLearningEngine
from app.quality.validation_engine import ValidationEngine
from app.showcase.certification import JarvisCertifier
from app.showcase.demo_runner import DemoRunner
from app.showcase.omega_benchmark import OmegaBenchmarkSuite
from app.showcase.progress_engine import LiveProgressEngine
from app.showcase.scorecard import ScorecardGenerator


class TestShowcaseAndOmegaBenchmarks(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.knowledge = Path(self.temp_dir.name) / "knowledge"
        self.val_engine = ValidationEngine(str(self.temp_dir.name), str(self.knowledge))
        self.learn_engine = AutonomousLearningEngine(str(self.knowledge))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_live_progress_engine_renders_bars(self):
        progress = LiveProgressEngine()
        progress.update_stage("Planner", 100.0, "COMPLETED")
        progress.update_stage("Executor", 75.0, "RUNNING")

        view = progress.render_progress_view()
        self.assertIn("Planner", view)
        self.assertIn("Executor", view)
        self.assertIn("100.0%", view)

    def test_scorecard_generator_9_factors(self):
        scorecard = ScorecardGenerator.generate_scorecard(
            project_name="Hospital ERP",
            requirement_analysis=96.0,
            planning=95.0,
            architecture=96.0,
            code_quality=95.0,
            testing=98.0,
            repair=96.0,
            performance=92.0,
            security=99.0,
            documentation=97.0,
        )

        self.assertGreaterEqual(scorecard["overall_score"], 95.0)
        self.assertEqual(scorecard["grade"], "A+")

        md = ScorecardGenerator.format_markdown(scorecard)
        self.assertIn("Enterprise Project Scorecard", md)
        self.assertIn("Requirement Analysis", md)

    def test_demo_runner_hospital_and_crm(self):
        runner = DemoRunner(self.val_engine, self.learn_engine)
        res = runner.run_demo("hospital")
        self.assertTrue(res.success)
        self.assertEqual(res.data["project"]["name"], "Hospital Management System")
        self.assertIn("scorecard", res.data)

    def test_omega_benchmark_suite_15_challenges(self):
        suite = OmegaBenchmarkSuite(self.val_engine, self.learn_engine)
        bench = suite.run_all_challenges()

        self.assertEqual(bench["total_challenges"], 15)
        self.assertEqual(bench["passed_challenges"], 15)
        self.assertEqual(bench["pass_rate_pct"], 100.0)
        self.assertTrue(bench["certified"])
        self.assertGreaterEqual(bench["average_score"], 95.0)

    def test_jarvis_certifier_production_ready(self):
        certifier = JarvisCertifier(self.val_engine, self.learn_engine)
        cert = certifier.certify_system()

        self.assertTrue(cert.success)
        self.assertTrue(cert.data["certified"])
        self.assertIn("Production Certification Report", cert.data["report_markdown"])
