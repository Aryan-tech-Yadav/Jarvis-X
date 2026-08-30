"""Tests for workflow.py."""

import pytest

from app.engineering.workflow import EngineeringWorkflow


class TestEngineeringWorkflow:
    def setup_method(self):
        self.workflow = EngineeringWorkflow(state_dir=".jarvis/test_states")

    def teardown_method(self):
        import shutil
        shutil.rmtree(".jarvis/test_states", ignore_errors=True)

    def test_run_hospital_workflow(self):
        result = self.workflow.run("Build Hospital Management System")
        assert result.success is True
        assert result.analysis is not None
        assert result.analysis['domain'] == 'hospital'
        assert result.architecture is not None
        assert result.task_breakdown is not None
        assert result.dependencies is not None
        assert result.execution_plan is not None
        assert result.report is not None
        assert result.report['overall_readiness'] > 0

    def test_run_api_workflow(self):
        result = self.workflow.run("Build REST API for ecommerce platform")
        assert result.success is True
        assert result.analysis['project_type'] == 'api'
        assert result.analysis['domain'] == 'ecommerce'

    def test_workflow_generates_report(self):
        result = self.workflow.run("Build social media platform")
        assert result.report is not None
        assert 'requirement_score' in result.report
        assert 'architecture_score' in result.report
        assert 'estimated_cost' in result.report
        assert 'estimated_time' in result.report

    def test_workflow_no_cycles(self):
        result = self.workflow.run("Build education platform")
        assert result.dependencies is not None
        assert result.dependencies['has_cycles'] is False

    def test_workflow_duration(self):
        result = self.workflow.run("Build finance dashboard")
        assert result.duration > 0
        assert result.duration < 60  # Should complete in under 60s

    def test_get_project_state(self):
        result = self.workflow.run("Build test project")
        assert result.workflow_id is not None
        state = self.workflow.get_project_state(result.workflow_id)
        assert state is not None
        assert state['project_id'] == result.workflow_id
