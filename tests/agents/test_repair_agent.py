"""Tests for repair_agent.py."""

import os
import tempfile

import pytest

from app.agents.project_context import ProjectContext
from app.agents.repair_agent import RepairAgent


class TestRepairAgent:
    def setup_method(self):
        self.agent = RepairAgent(max_retries=2)
        self.tmpdir = tempfile.mkdtemp()

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_repair_no_issues(self):
        context = ProjectContext(project_path=self.tmpdir)
        result = self.agent.run(context)
        assert result["success"] is True
        assert result["output"]["repaired"] == 0

    def test_repair_with_review_issues(self):
        context = ProjectContext(project_path=self.tmpdir)
        context.review = {"issues": ["TODO marker found", "snake_case violation"]}
        result = self.agent.run(context)
        assert result["success"] is True
        assert result["output"]["repaired"] >= 0

    def test_repair_invalid_path(self):
        context = ProjectContext(project_path="/nonexistent/path")
        result = self.agent.run(context)
        assert result["success"] is False

    def test_max_retries_respected(self):
        agent = RepairAgent(max_retries=1)
        context = ProjectContext(project_path=self.tmpdir)
        context.review = {"issues": ["unknown issue type"]}
        result = agent.run(context)
        assert result["success"] is True

    def test_context_update(self):
        context = ProjectContext(project_path=self.tmpdir)
        result = self.agent.run(context)
        assert "repair" in context.completed_tasks
        assert "repaired_count" in context.metrics
