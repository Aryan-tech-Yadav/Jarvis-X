"""Unit tests for Self-Repair Engine and Self-Repair Memory."""

import tempfile
import unittest
from pathlib import Path

from app.quality.repair_engine import RepairEngine, SelfRepairMemory
from app.quality.root_cause_engine import RootCauseEngine


class TestRepairEngine(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.knowledge = self.root / "knowledge"
        self.engine = RepairEngine(str(self.root), str(self.knowledge))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_self_repair_memory_record_and_lookup(self):
        mem = SelfRepairMemory(str(self.knowledge))
        rec = mem.record_repair(
            problem="Missing Configuration 'db_host'",
            fix="Loaded default config",
            success=True,
            repair_time_sec=1.5,
            error_category="config",
            failing_symbol="db_host",
        )
        self.assertEqual(rec["success"], "YES")

        found = mem.lookup_similar_repair("Missing Configuration 'db_host'", "config", "db_host")
        self.assertIsNotNone(found)
        self.assertEqual(found["fix"], "Loaded default config")

        stats = mem.get_stats()
        self.assertEqual(stats["total_repairs"], 1)
        self.assertEqual(stats["successful_repairs"], 1)

    def test_repair_missing_config_scenario(self):
        source_code = """def get_database_host(config):
    return config['db_host']
"""
        test_code = """import unittest
import target_mod

class TestConfig(unittest.TestCase):
    def test_empty_config(self):
        host = target_mod.get_database_host({})
        self.assertIsNotNone(host)
"""
        res = self.engine.repair_and_retest(source_code, test_code, module_name="target_mod")
        self.assertTrue(res.original_failed)
        self.assertTrue(res.final_success)
        self.assertGreater(len(res.repairs_attempted), 0)
        self.assertTrue(res.knowledge_saved)

    def test_repair_missing_import_scenario(self):
        source_code = """def get_square_root(val):
    return math.sqrt(val)
"""
        test_code = """import unittest
import target_mod

class TestMath(unittest.TestCase):
    def test_sqrt(self):
        res = target_mod.get_square_root(16)
        self.assertEqual(res, 4.0)
"""
        res = self.engine.repair_and_retest(source_code, test_code, module_name="target_mod")
        self.assertTrue(res.original_failed)
        self.assertTrue(res.final_success)

    def test_repair_syntax_typo_scenario(self):
        source_code = """def compute_total(a, b)
    return a + b
"""
        test_code = """import unittest
import target_mod

class TestTotal(unittest.TestCase):
    def test_total(self):
        self.assertEqual(target_mod.compute_total(2, 3), 5)
"""
        res = self.engine.repair_and_retest(source_code, test_code, module_name="target_mod")
        self.assertTrue(res.original_failed)
        self.assertTrue(res.final_success)
