"""Tests for execution_planner.py."""

import pytest

from app.engineering.execution_planner import ExecutionPlanner


class TestExecutionPlanner:
    def setup_method(self):
        self.planner = ExecutionPlanner()

    def test_plan_web_project(self):
        task_breakdown = type('obj', (object,), {
            'project_name': 'Test Web App',
            'tasks': [
                type('t', (object,), {'id': 'TASK-001', 'category': 'setup', 'estimated_hours': 1.0})(),
                type('t', (object,), {'id': 'TASK-002', 'category': 'backend', 'estimated_hours': 2.0})(),
            ],
            'to_dict': lambda self: {},
        })()
        resolved = type('obj', (object,), {
            'parallel_groups': [['TASK-001'], ['TASK-002']],
            'critical_path': ['TASK-001', 'TASK-002'],
        })()
        plan = self.planner.plan(task_breakdown, resolved)
        from app.engineering.execution_planner import ExecutionPlan
        assert isinstance(plan, ExecutionPlan)
        assert plan.total_phases > 0

    def test_phases_created(self):
        task_breakdown = type('obj', (object,), {
            'project_name': 'Test API',
            'tasks': [
                type('t', (object,), {'id': 'TASK-001', 'category': 'setup', 'estimated_hours': 1.0})(),
                type('t', (object,), {'id': 'TASK-002', 'category': 'backend', 'estimated_hours': 2.0})(),
                type('t', (object,), {'id': 'TASK-003', 'category': 'testing', 'estimated_hours': 3.0})(),
            ],
            'to_dict': lambda self: {},
        })()
        resolved = type('obj', (object,), {
            'parallel_groups': [],
            'critical_path': [],
        })()
        plan = self.planner.plan(task_breakdown, resolved)
        phase_names = [p.name for p in plan.phases]
        assert any("Foundation" in name for name in phase_names)
        assert any("Backend" in name for name in phase_names)

    def test_total_hours_calculated(self):
        task_breakdown = type('obj', (object,), {
            'project_name': 'Test',
            'tasks': [
                type('t', (object,), {'id': 'TASK-001', 'category': 'setup', 'estimated_hours': 1.0})(),
            ],
            'to_dict': lambda self: {},
        })()
        resolved = type('obj', (object,), {
            'parallel_groups': [],
            'critical_path': [],
        })()
        plan = self.planner.plan(task_breakdown, resolved)
        assert plan.total_estimated_hours > 0

    def test_to_dict(self):
        task_breakdown = type('obj', (object,), {
            'project_name': 'Test',
            'tasks': [
                type('t', (object,), {'id': 'TASK-001', 'category': 'setup', 'estimated_hours': 1.0})(),
            ],
            'to_dict': lambda self: {},
        })()
        resolved = type('obj', (object,), {
            'parallel_groups': [],
            'critical_path': [],
        })()
        plan = self.planner.plan(task_breakdown, resolved)
        data = plan.to_dict()
        assert 'phases' in data
        assert 'total_phases' in data
