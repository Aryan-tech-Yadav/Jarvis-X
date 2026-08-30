"""Tests for risk_engine.py."""

import pytest

from app.self_improvement.risk_engine import RiskEngine, RiskAssessment


class TestRiskEngine:
    def setup_method(self):
        self.engine = RiskEngine()

    def test_assess_low_risk_task(self):
        task = {"id": "t1", "type": "documentation", "risk": "low", "effort": "low", "file": "docs/readme.md"}
        assessment = self.engine.assess(task)
        assert isinstance(assessment, RiskAssessment)
        assert assessment.risk_level == "low"
        assert assessment.requires_approval is False

    def test_assess_high_risk_task(self):
        task = {"id": "t2", "type": "refactor", "risk": "high", "effort": "high", "file": "app/core/brain_manager.py"}
        assessment = self.engine.assess(task)
        assert assessment.risk_level == "high"
        assert assessment.requires_approval is True

    def test_assess_core_module(self):
        task = {"id": "t3", "type": "refactor", "risk": "medium", "effort": "medium", "file": "app/kernel/kernel.py"}
        assessment = self.engine.assess(task)
        assert "Core module modification" in assessment.factors

    def test_assess_complex_file(self):
        complex_code = "def test():\n" + "    if True:\n" * 20 + "        pass\n"
        task = {"id": "t4", "type": "refactor", "risk": "medium", "effort": "medium", "file": "app/test.py"}
        assessment = self.engine.assess(task, file_content=complex_code)
        assert "High cyclomatic complexity" in assessment.factors or "Large file" in assessment.factors

    def test_assess_batch(self):
        tasks = [
            {"id": "t1", "type": "bug", "risk": "low", "effort": "low", "file": "app/a.py"},
            {"id": "t2", "type": "refactor", "risk": "high", "effort": "high", "file": "app/b.py"},
        ]
        assessments = self.engine.assess_batch(tasks)
        assert len(assessments) == 2
        assert assessments[0].risk_level == "low"
        assert assessments[1].risk_level == "high"

    def test_assessment_to_dict(self):
        task = {"id": "t1", "type": "bug", "risk": "low", "effort": "low", "file": "app/a.py"}
        assessment = self.engine.assess(task)
        data = assessment.to_dict()
        assert "task_id" in data
        assert "risk_level" in data
        assert "requires_approval" in data
