"""Unit tests for Performance Engine."""

import tempfile
import unittest
from pathlib import Path

from app.quality.performance_engine import PerformanceEngine


class TestPerformanceEngine(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.engine = PerformanceEngine(str(self.root))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_profile_callable_measures_runtime_and_memory(self):
        def sample_workload():
            data = [x * 2 for x in range(10000)]
            return sum(data)

        res, perf = self.engine.profile_callable(sample_workload)
        self.assertEqual(res, sum(x * 2 for x in range(10000)))
        self.assertGreaterEqual(perf.performance_score, 90.0)
        self.assertGreater(perf.memory_bytes, 0)

    def test_static_performance_detects_nested_loops_and_n1_queries(self):
        code = """def fetch_user_orders(users, db):
    results = []
    for u in users:
        orders = db.query(f"SELECT * FROM orders WHERE user_id = {u.id}")
        for o in orders:
            for item in o.items:
                results.append(item)
    return results
"""
        src = self.root / "orders.py"
        src.write_text(code, encoding="utf-8")

        perf = self.engine.analyze_static_performance(str(self.root))
        self.assertGreater(perf.db_query_count, 0)
        self.assertTrue(any(b.get("type") == "nested_loop_complexity" for b in perf.bottlenecks))
        self.assertTrue(any(b.get("type") == "n_plus_one_query" for b in perf.bottlenecks))
        self.assertGreater(len(perf.suggestions), 0)
