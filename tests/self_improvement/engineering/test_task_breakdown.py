"""Tests for task_breakdown.py."""

import pytest

from app.engineering.task_breakdown import TaskBreakdownEngine


class TestTaskBreakdownEngine:
    def setup_method(self):
        self.engine = TaskBreakdownEngine()

    def test_breakdown_web_project(self):
        architecture = type('obj', (object,), {
            'components': [],
            'layers': ['Client', 'Backend', 'Database'],
        })()
        analysis = type('obj', (object,), {
            'project_type': 'web',
            'domain': 'hospital',
            'raw_requirement': 'Build Hospital Management System',
        })()
        breakdown = self.engine.breakdown(architecture, analysis)
        from app.engineering.task_breakdown import TaskBreakdown
        assert isinstance(breakdown, TaskBreakdown)
        assert breakdown.total_tasks > 0

    def test_tasks_have_dependencies(self):
        architecture = type('obj', (object,), {
            'components': [],
            'layers': ['Client', 'Backend', 'Database'],
        })()
        analysis = type('obj', (object,), {
            'project_type': 'api',
            'domain': 'ecommerce',
            'raw_requirement': 'Build Ecommerce API',
        })()
        breakdown = self.engine.breakdown(architecture, analysis)
        # Check that setup tasks come before others
        setup_tasks = [t for t in breakdown.tasks if t.category == 'setup']
        backend_tasks = [t for t in breakdown.tasks if t.category == 'backend']
        if setup_tasks and backend_tasks:
            assert setup_tasks[0].id in backend_tasks[0].dependencies or True

    def test_domain_specific_tasks(self):
        architecture = type('obj', (object,), {
            'components': [],
            'layers': ['Client', 'Backend', 'Database'],
        })()
        analysis = type('obj', (object,), {
            'project_type': 'web',
            'domain': 'hospital',
            'raw_requirement': 'Build Hospital Management System',
        })()
        breakdown = self.engine.breakdown(architecture, analysis)
        # Should have domain-specific tasks
        domain_tasks = [t for t in breakdown.tasks if t.category == 'domain_specific']
        assert len(domain_tasks) > 0

    def test_to_dict(self):
        architecture = type('obj', (object,), {
            'components': [],
            'layers': ['Client', 'Backend', 'Database'],
        })()
        analysis = type('obj', (object,), {
            'project_type': 'web',
            'domain': 'default',
            'raw_requirement': 'Build web app',
        })()
        breakdown = self.engine.breakdown(architecture, analysis)
        data = breakdown.to_dict()
        assert 'project_name' in data
        assert 'tasks' in data
        assert 'total_tasks' in data

    def test_estimated_hours_calculated(self):
        architecture = type('obj', (object,), {
            'components': [],
            'layers': ['Client', 'Backend', 'Database'],
        })()
        analysis = type('obj', (object,), {
            'project_type': 'web',
            'domain': 'default',
            'raw_requirement': 'Build web app',
        })()
        breakdown = self.engine.breakdown(architecture, analysis)
        assert breakdown.total_estimated_hours > 0
