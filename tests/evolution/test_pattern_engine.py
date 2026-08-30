"""Unit tests for Success Pattern Engine."""

import tempfile
import unittest
from pathlib import Path

from app.evolution.models.pattern import PatternType
from app.evolution.success_engine import SuccessPatternEngine


class TestPatternEngine(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.knowledge_dir = Path(self.temp_dir.name) / "knowledge"
        self.engine = SuccessPatternEngine(str(self.knowledge_dir))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_default_seeded_patterns_and_query(self):
        patterns = self.engine.list_patterns()
        self.assertGreaterEqual(len(patterns), 3)

        arch = self.engine.find_recommended_architecture("erp")
        self.assertIsNotNone(arch)
        self.assertIn("FastAPI", arch.name)
        self.assertGreaterEqual(arch.benchmark_score, 95.0)

    def test_register_and_record_pattern_usage(self):
        p = self.engine.register_pattern(
            name="Microservice Event Broker",
            pattern_type=PatternType.ARCHITECTURE,
            domain="messaging",
            blueprint={"broker": "redis_pubsub"},
            benchmark_score=94.0,
        )
        self.assertEqual(p.name, "Microservice Event Broker")

        updated = self.engine.record_pattern_usage(p.pattern_id, success=True, benchmark_score=98.0)
        self.assertEqual(updated.times_used, 2)
        self.assertEqual(updated.success_rate, 1.0)
