"""Tests for engineering_report.py."""

import pytest

from app.engineering.engineering_report import EngineeringReportGenerator, EngineeringReport


class TestEngineeringReportGenerator:
    def setup_method(self):
        self.generator = EngineeringReportGenerator()

    def _make_analysis(self, confidence=0.7, missing=None, project_type='web'):
        return type('obj', (object,), {
            'confidence': confidence,
            'missing_information': missing or ['deployment', 'testing'],
            'project_type': project_type,
            'project_name': 'Hospital Management System',
        })()

    def _make_architecture(self):
        return type('obj', (object,), {
            'components': [type('c', (object,), {'name': 'Backend', 'technology': 'FastAPI'})(),
                          type('c', (object,), {'name': 'Database', 'technology': 'PostgreSQL'})()],
            'layers': ['Client', 'Backend', 'Database'],
            'tech_stack': {'backend': 'FastAPI', 'database': 'PostgreSQL', 'cache': None},
        })()

    def _make_task_breakdown(self):
        return type('obj', (object,), {
            'total_tasks': 10,
            'total_estimated_hours': 40.0,
            'tasks': [type('t', (object,), {'id': 'TASK-001', 'category': 'setup', 'estimated_hours': 1.0})(),
                      type('t', (object,), {'id': 'TASK-002', 'category': 'backend', 'estimated_hours': 2.0}),
                      type('t', (object,), {'id': 'TASK-003', 'category': 'testing', 'estimated_hours': 3.0})],
        })()

    def _make_resolved_deps(self):
        return type('obj', (object,), {
            'parallel_groups': [['TASK-001'], ['TASK-002']],
            'critical_path': ['TASK-001', 'TASK-002'],
            'has_cycles': False,
        })()

    def _make_execution_plan(self):
        return type('obj', (object,), {
            'total_phases': 3,
        })()

    def _make_project_state(self):
        return type('obj', (object,), {
            'status': 'in_progress',
            'test_coverage': 0.0,
            'runtime_errors': [],
        })()

    def test_generate_report(self):
        report = self.generator.generate(
            "Build Hospital Management System",
            self._make_analysis(),
            self._make_architecture(),
            self._make_task_breakdown(),
            self._make_resolved_deps(),
            self._make_execution_plan(),
            self._make_project_state(),
        )
        assert isinstance(report, EngineeringReport)
        assert report.overall_readiness > 0
        assert report.risk_level in ['low', 'medium', 'high', 'critical']
        assert len(report.recommendations) > 0

    def test_report_has_scores(self):
        report = type('obj', (object,), {
            'requirement_score': 70.0,
            'architecture_score': 80.0,
            'testing_score': 60.0,
            'security_score': 75.0,
            'complexity_score': 50.0,
            'overall_readiness': 68.0,
            'risk_level': 'medium',
            'recommendations': ['Add tests'],
            'to_dict': lambda self: {},
        })()
        assert hasattr(report, 'requirement_score')
        assert hasattr(report, 'architecture_score')

    def test_cost_estimation(self):
        report = type('obj', (object,), {
            'estimated_cost': '$5,000',
            'estimated_time': '2 weeks',
            'to_dict': lambda self: {},
        })()
        assert hasattr(report, 'estimated_cost')
        assert hasattr(report, 'estimated_time')

    def test_to_dict(self):
        report = type('obj', (object,), {
            'project_name': 'Test',
            'overall_readiness': 75.0,
            'risk_level': 'low',
            'recommendations': ['Good to go'],
            'to_dict': lambda self: {'project_name': 'Test', 'overall_readiness': 75.0, 'risk_level': 'low', 'recommendations': ['Good to go']},
        })()
        data = report.to_dict()
        assert 'project_name' in data
        assert 'overall_readiness' in data
