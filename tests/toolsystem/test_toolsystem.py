"""Unit tests for Tool Orchestration Engine (TOE)."""

import tempfile
import unittest
from pathlib import Path

from app.toolsystem.tool_capability import ToolCapability, ToolRisk
from app.toolsystem.tool_executor import ToolExecutor
from app.toolsystem.tool_metrics import ToolMetricsTracker
from app.toolsystem.tool_policy import ToolPolicy
from app.toolsystem.tool_registry import ToolRegistry
from app.toolsystem.tool_report import ToolReport
from app.toolsystem.tool_router import ToolRouter
from app.toolsystem.tool_selector import ToolSelector
from app.toolsystem.tool_validator import ToolValidator


class TestToolSystem(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.registry = ToolRegistry()
        self.policy = ToolPolicy(str(self.root))
        self.executor = ToolExecutor(self.registry, self.policy)
        self.selector = ToolSelector(self.registry)
        self.router = ToolRouter(self.selector, self.executor)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_tool_selector_intent_matching(self):
        tool = self.selector.select_tool_for_task("Need Dockerfile and container config")
        self.assertIsNotNone(tool)
        self.assertEqual(tool.name, "docker")

        tool_git = self.selector.select_tool_for_task("Need Git Commit and branch")
        self.assertIsNotNone(tool_git)
        self.assertEqual(tool_git.name, "git")

        tool_db = self.selector.select_tool_for_task("Need SQL Schema migration")
        self.assertIsNotNone(tool_db)
        self.assertEqual(tool_db.name, "database")

    def test_tool_executor_filesystem_and_validation(self):
        target_file = self.root / "sample.txt"
        res = self.executor.execute_tool(
            "filesystem",
            action="write",
            path=str(target_file),
            content="Hello autonomous tools!",
        )
        self.assertTrue(res.success)
        self.assertTrue(ToolValidator.validate_filesystem_output(str(target_file)))

        read_res = self.executor.execute_tool(
            "filesystem",
            action="read",
            path=str(target_file),
        )
        self.assertTrue(read_res.success)
        self.assertEqual(read_res.data["content"], "Hello autonomous tools!")

    def test_tool_policy_blocks_forbidden_commands(self):
        self.assertFalse(self.policy.is_command_safe("rm -rf /"))
        self.assertTrue(self.policy.is_command_safe("pytest tests/"))

    def test_terminal_handler_rejects_shell_operators(self):
        result = self.executor.execute_tool(
            "terminal", command="echo hello; whoami"
        )
        self.assertFalse(result.success)

    def test_terminal_handler_rejects_destructive_commands(self):
        result = self.executor.execute_tool("terminal", command="rm -rf /")
        self.assertFalse(result.success)

    def test_terminal_handler_marks_simulated_result(self):
        result = self.executor.execute_tool("terminal", command="echo hello")
        self.assertTrue(result.success)
        self.assertTrue(result.data["simulated"])

    def test_terminal_handler_rejects_unknown_command(self):
        result = self.executor.execute_tool(
            "terminal", command="unknown-command --help"
        )
        self.assertFalse(result.success)

    def test_tool_router_multi_step_pipeline(self):
        steps = [
            {"name": "create_dir", "tool": "filesystem", "kwargs": {"action": "write", "path": str(self.root / "init.py"), "content": "# Init"}},
            {"name": "validate_git", "tool": "git", "kwargs": {"command": "status"}},
            {"name": "validate_docker", "tool": "docker", "kwargs": {"action": "validate"}},
        ]
        res = self.router.execute_pipeline(steps)
        self.assertTrue(res.success)
        self.assertEqual(len(res.data["pipeline_results"]), 3)

    def test_tool_metrics_and_report_generation(self):
        tracker = ToolMetricsTracker()
        tracker.record_call("git", success=True, duration_sec=0.12)
        tracker.record_call("docker", success=True, duration_sec=0.45)
        tracker.record_call("python", success=False, duration_sec=0.30, retries=1)

        summary = tracker.get_summary()
        self.assertEqual(summary["git"]["total_calls"], 1)
        self.assertEqual(summary["python"]["failure_count"], 1)

        report_md = ToolReport.generate_report(summary)
        self.assertIn("Tool Orchestration & Execution Report", report_md)
        self.assertIn("Docker", report_md)
