"""Tests for multi-agent orchestrator."""

import os
import tempfile
from unittest.mock import patch

import pytest

from app.engineering.architecture_agent import ArchitectureDesign
from app.orchestrator.orchestrator import MultiAgentOrchestrator, OrchestratorResult


def _fake_ai_ask(self, prompt):
    """Fast fake AI response for tests."""
    return '{"folders": ["backend", "frontend", "tests", "docs", "docker"], "architecture": {"pattern": "layered monolith", "layers": ["presentation", "application", "domain", "infrastructure"], "description": "Test architecture"}}'


class TestMultiAgentOrchestrator:
    def setup_method(self):
        self.orchestrator = MultiAgentOrchestrator()
        self.tmpdir = tempfile.mkdtemp()

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_run_hospital_system(self):
        with patch("app.ai.ai_manager.AIManager.ask", _fake_ai_ask):
            result = self.orchestrator.run("Build Hospital Management System", base_path=self.tmpdir)
        assert isinstance(result, OrchestratorResult)
        assert len(result.agents_executed) > 0
        assert "architect" in result.agents_executed
        assert "backend" in result.agents_executed

    def test_run_ecommerce_platform(self):
        with patch("app.ai.ai_manager.AIManager.ask", _fake_ai_ask):
            result = self.orchestrator.run("Build E-Commerce Platform", base_path=self.tmpdir)
        assert result.workflow_id is not None
        assert result.duration > 0

    def test_project_path_created(self):
        with patch("app.ai.ai_manager.AIManager.ask", _fake_ai_ask):
            result = self.orchestrator.run("Build Test Project", base_path=self.tmpdir)
        if result.success:
            assert result.project_path != ""

    def test_agents_executed_in_order(self):
        with patch("app.ai.ai_manager.AIManager.ask", _fake_ai_ask):
            result = self.orchestrator.run("Build Test Project", base_path=self.tmpdir)
        expected_order = ["architect", "database", "backend", "frontend"]
        executed = result.agents_executed
        for agent in expected_order:
            if agent in executed:
                idx = executed.index(agent)
                for prev_agent in expected_order[:expected_order.index(agent)]:
                    if prev_agent in executed:
                        assert executed.index(prev_agent) < idx

    def test_result_to_dict(self):
        with patch("app.ai.ai_manager.AIManager.ask", _fake_ai_ask):
            result = self.orchestrator.run("Build Test Project", base_path=self.tmpdir)
        data = result.to_dict()
        assert "workflow_id" in data
        assert "success" in data
        assert "duration" in data
