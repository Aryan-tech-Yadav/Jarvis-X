"""End-to-End Integration Test for EPIC-004 Autonomous QA & Self-Healing Pipeline."""

import tempfile
import unittest
from pathlib import Path

from app.quality.validation_engine import ValidationEngine


class TestQualityEndToEndIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.knowledge = self.root / "knowledge"
        self.engine = ValidationEngine(str(self.root), str(self.knowledge))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_complete_autonomous_repair_and_validation_lifecycle(self):
        """Complete Scenario:

        1. Generate Project / Module with a bug (Missing config key)
        2. Run Tests -> Fails initially
        3. Root Cause Identified (Missing Configuration 'db_host')
        4. Repair Synthesized & Applied
        5. Retest -> Passes with 100% success
        6. Security Scan & Performance Scan Pass
        7. Benchmark Recorded
        8. Release Gate Evaluates -> ACCEPTED
        9. Quality Report Produced across Formats
        """
        source_code = '''"""Database Connection Manager."""

def get_database_url(config):
    """Returns database connection URL."""
    host = config['db_host']
    port = config.get('port', 5432)
    return f"postgres://{host}:{port}/app"
'''

        test_code = '''import unittest
import target_mod

class TestDatabaseConnection(unittest.TestCase):
    def test_url_with_empty_config(self):
        url = target_mod.get_database_url({})
        self.assertIsNotNone(url)
        self.assertTrue("postgres://" in url)
'''

        # Run full validation pipeline
        exec_res, report = self.engine.validate_code_snippet(
            source_code=source_code,
            test_code=test_code,
            module_name="target_mod",
            version="v1.0.0",
        )

        # Assert pipeline success and release acceptance
        self.assertTrue(exec_res.success)
        self.assertIn("Validation PASSED", exec_res.message)
        self.assertIsNotNone(report.quality_score)
        self.assertTrue(report.quality_score.passed_gate)
        self.assertGreaterEqual(report.quality_score.overall_score, 88.0)

        # Assert self-healing details
        self.assertIsNotNone(report.self_healing_result)
        self.assertTrue(report.self_healing_result.original_failed)
        self.assertTrue(report.self_healing_result.final_success)
        self.assertEqual(report.self_healing_result.root_cause.error_category, "config")
        self.assertTrue(report.self_healing_result.knowledge_saved)

        # Assert benchmark tracking
        history = self.engine.benchmark_validator.get_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["version"], "v1.0.0")

        # Assert report formatting
        md = report.to_markdown()
        self.assertIn("RELEASE ACCEPTED", md)
        self.assertIn("Self-Healing & Automated Repair", md)
