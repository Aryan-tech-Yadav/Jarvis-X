"""Unit tests for Security Engine."""

import tempfile
import unittest
from pathlib import Path

from app.quality.models import IssueSeverity
from app.quality.security_engine import SecurityEngine


class TestSecurityEngine(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.engine = SecurityEngine(str(self.root))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_detect_hardcoded_secrets(self):
        code = """def connect_api():
    api_key = "sk-1234567890abcdef1234567890abcdef"
    return api_key
"""
        src = self.root / "auth.py"
        src.write_text(code, encoding="utf-8")

        res = self.engine.scan_directory(str(self.root))
        self.assertFalse(res.passed)
        self.assertGreater(res.secrets_found, 0)
        self.assertTrue(any(v.severity == IssueSeverity.CRITICAL for v in res.vulnerabilities))

    def test_detect_sql_injection(self):
        code = """def query_user(cursor, user_id):
    cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
"""
        src = self.root / "repo.py"
        src.write_text(code, encoding="utf-8")

        res = self.engine.scan_directory(str(self.root))
        self.assertFalse(res.passed)
        self.assertGreater(res.sql_injections, 0)
        self.assertTrue(any(v.rule == "sql_injection" for v in res.vulnerabilities))

    def test_detect_dynamic_execution_and_command_injection(self):
        code = """import os, subprocess

def run_cmd(user_arg):
    os.system(f"echo {user_arg}")
    eval(user_arg)
    subprocess.Popen(user_arg, shell=True)
"""
        src = self.root / "cmd.py"
        src.write_text(code, encoding="utf-8")

        res = self.engine.scan_directory(str(self.root))
        self.assertFalse(res.passed)
        self.assertGreater(res.command_injections, 0)

    def test_detect_unsafe_deserialization(self):
        code = """import pickle

def load_payload(raw_bytes):
    return pickle.loads(raw_bytes)
"""
        src = self.root / "deser.py"
        src.write_text(code, encoding="utf-8")

        res = self.engine.scan_directory(str(self.root))
        self.assertFalse(res.passed)
        self.assertGreater(res.deserialization_risks, 0)

    def test_clean_security_scan(self):
        code = """import os

def clean_get_key():
    return os.environ.get("MY_API_KEY", "")
"""
        src = self.root / "clean.py"
        src.write_text(code, encoding="utf-8")

        res = self.engine.scan_directory(str(self.root))
        self.assertTrue(res.passed)
        self.assertEqual(res.security_score, 100.0)
