"""Unit tests for Root Cause Diagnostic Engine."""

import unittest

from app.quality.root_cause_engine import RootCauseEngine


class TestRootCauseEngine(unittest.TestCase):
    def setUp(self):
        self.engine = RootCauseEngine()

    def test_diagnose_missing_config_key_error(self):
        fail_msg = "KeyError: 'db_host'"
        tb = """Traceback (most recent call last):
  File "app/database.py", line 14, in connect
    host = config['db_host']
KeyError: 'db_host'
"""
        res = self.engine.diagnose(fail_msg, tb)
        self.assertEqual(res.error_category, "config")
        self.assertEqual(res.failing_symbol, "db_host")
        self.assertIn("db_host", res.root_cause)
        self.assertGreaterEqual(res.confidence, 0.90)
        self.assertIn("default", res.repair_strategy.lower())

    def test_diagnose_missing_import_module(self):
        fail_msg = "ModuleNotFoundError: No module named 'math_utils'"
        tb = """Traceback (most recent call last):
  File "app/service.py", line 3, in <module>
    import math_utils
ModuleNotFoundError: No module named 'math_utils'
"""
        res = self.engine.diagnose(fail_msg, tb)
        self.assertEqual(res.error_category, "import")
        self.assertEqual(res.failing_symbol, "math_utils")
        self.assertGreaterEqual(res.confidence, 0.95)

    def test_diagnose_attribute_error(self):
        fail_msg = "AttributeError: 'Service' object has no attribute 'process_data'"
        tb = """Traceback (most recent call last):
  File "main.py", line 22, in run
    service.process_data()
AttributeError: 'Service' object has no attribute 'process_data'
"""
        res = self.engine.diagnose(fail_msg, tb)
        self.assertEqual(res.error_category, "attribute")
        self.assertEqual(res.failing_symbol, "process_data")
        self.assertGreaterEqual(res.confidence, 0.90)

    def test_diagnose_syntax_error(self):
        fail_msg = "SyntaxError: invalid syntax"
        tb = """Traceback (most recent call last):
  File "broken.py", line 5
    def broken_func()
                    ^
SyntaxError: invalid syntax
"""
        res = self.engine.diagnose(fail_msg, tb)
        self.assertEqual(res.error_category, "syntax")
        self.assertGreaterEqual(res.confidence, 0.95)

    def test_diagnose_zero_division(self):
        fail_msg = "ZeroDivisionError: division by zero"
        tb = """Traceback (most recent call last):
  File "calc.py", line 8, in divide
    return a / b
ZeroDivisionError: division by zero
"""
        res = self.engine.diagnose(fail_msg, tb)
        self.assertEqual(res.error_category, "math")
        self.assertIn("guard", res.repair_strategy.lower())
