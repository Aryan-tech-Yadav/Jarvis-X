"""Tests for AgentSandbox isolated execution and credential stripping."""

import os
import tempfile
import unittest

from app.agents.sandbox import AgentSandbox


class TestAgentSandboxExecution(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.sandbox = AgentSandbox(self.tmpdir.name)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_path_confinement_and_rejection(self):
        self.assertTrue(self.sandbox.contains("valid.py"))
        self.assertTrue(self.sandbox.contains("sub/valid.py"))
        self.assertFalse(self.sandbox.contains("../outside.py"))
        with self.assertRaises(PermissionError):
            self.sandbox.path("../outside.py")

    def test_execute_code_success(self):
        res = self.sandbox.execute_code("print('sandbox-ok')")
        self.assertTrue(res["success"])
        self.assertIn("sandbox-ok", res["stdout"])
        self.assertEqual(res["returncode"], 0)

    def test_execute_code_strips_sensitive_secrets(self):
        os.environ["API_KEY"] = "super-secret-key"
        os.environ["CUSTOM_SECRET_TOKEN"] = "hidden-token"
        try:
            code = (
                "import os\n"
                "print('API_KEY:', os.getenv('API_KEY'))\n"
                "print('TOKEN:', os.getenv('CUSTOM_SECRET_TOKEN'))\n"
            )
            res = self.sandbox.execute_code(code)
            self.assertTrue(res["success"])
            self.assertIn("API_KEY: None", res["stdout"])
            self.assertIn("TOKEN: None", res["stdout"])
        finally:
            os.environ.pop("API_KEY", None)
            os.environ.pop("CUSTOM_SECRET_TOKEN", None)

    def test_execute_code_timeout_bounds(self):
        code = "import time\ntime.sleep(5)\nprint('done')"
        res = self.sandbox.execute_code(code, timeout=1.0)
        self.assertFalse(res["success"])
        self.assertTrue(res["timed_out"])
        self.assertIn("timed out", res["stderr"].lower())

