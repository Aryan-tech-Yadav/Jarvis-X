"""Unit tests for Failure Database Engine."""

import tempfile
import unittest
from pathlib import Path

from app.evolution.failure_engine import FailureEngine
from app.evolution.models.failure import FailureCategory


class TestFailureEngine(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.knowledge_dir = Path(self.temp_dir.name) / "knowledge"
        self.engine = FailureEngine(str(self.knowledge_dir))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_record_failure_and_find_direct_solution(self):
        f = self.engine.record_failure(
            problem="Circular Import between Models and Views",
            reason="Models imported Views directly",
            root_cause="Tight cross-layer coupling",
            fix_strategy="Move shared interfaces to core module",
            success=True,
            repair_time_sec=2.5,
            category=FailureCategory.IMPORT,
            failing_symbol="views",
        )

        self.assertEqual(f.problem, "Circular Import between Models and Views")

        # Lookup direct solution
        sol = self.engine.find_direct_solution("Circular Import", FailureCategory.IMPORT, "views")
        self.assertIsNotNone(sol)
        self.assertEqual(sol.fix_strategy, "Move shared interfaces to core module")

    def test_failure_occurrence_counter(self):
        self.engine.record_failure(
            problem="Missing Config Key",
            reason="Missing DB_PORT",
            root_cause="KeyError",
            fix_strategy="Use config.get",
            category=FailureCategory.CONFIGURATION,
        )
        # Record identical failure again
        rec2 = self.engine.record_failure(
            problem="Missing Config Key",
            reason="Missing DB_PORT",
            root_cause="KeyError",
            fix_strategy="Use config.get",
            category=FailureCategory.CONFIGURATION,
        )
        self.assertEqual(rec2.occurrences, 2)
