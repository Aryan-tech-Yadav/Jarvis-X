"""Tests for testing_agent.py."""

import os
import tempfile

import pytest

from app.agents.project_context import ProjectContext
from app.agents.testing_agent import TestingAgent


class TestTestingAgent:
    def setup_method(self):
        self.agent = TestingAgent()
        self.tmpdir = tempfile.mkdtemp()

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_skip_no_project_path(self):
        context = ProjectContext(project_path="")
        result = self.agent.run(context)
        assert result["success"] is True
        assert result["output"]["skipped"] is True

    def test_skip_no_source_files(self):
        context = ProjectContext(project_path=self.tmpdir)
        result = self.agent.run(context)
        assert result["success"] is True

    def test_generate_and_run_tests(self):
        # Create a simple source file
        src_dir = os.path.join(self.tmpdir, "src")
        os.makedirs(src_dir)
        with open(os.path.join(src_dir, "main.py"), "w") as f:
            f.write("def hello():\n    return 'hello'\n")

        context = ProjectContext(project_path=self.tmpdir)
        result = self.agent.run(context)
        assert result["success"] is True
        output = result["output"]
        assert output["test_files"] > 0
        assert output["passed"] > 0

    def test_context_updated(self):
        context = ProjectContext(project_path=self.tmpdir)
        result = self.agent.run(context)
        assert "testing" in context.completed_tasks
        assert "skipped" in context.metrics or "test_files" in context.metrics
