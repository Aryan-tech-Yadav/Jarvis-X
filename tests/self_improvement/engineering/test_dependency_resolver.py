"""Tests for dependency_resolver.py."""

import pytest

from app.engineering.dependency_resolver import DependencyResolver


class TestDependencyResolver:
    def setup_method(self):
        self.resolver = DependencyResolver()

    def test_resolve_no_dependencies(self):
        tasks = [
            {"id": "TASK-001", "dependencies": [], "estimated_hours": 1.0},
            {"id": "TASK-002", "dependencies": [], "estimated_hours": 2.0},
        ]
        result = self.resolver.resolve(tasks)
        assert len(result.ordered_tasks) == 2
        assert not result.has_cycles

    def test_resolve_with_dependencies(self):
        tasks = [
            {"id": "TASK-001", "dependencies": [], "estimated_hours": 1.0},
            {"id": "TASK-002", "dependencies": ["TASK-001"], "estimated_hours": 2.0},
            {"id": "TASK-003", "dependencies": ["TASK-002"], "estimated_hours": 3.0},
        ]
        result = self.resolver.resolve(tasks)
        assert not result.has_cycles
        assert result.ordered_tasks.index("TASK-001") < result.ordered_tasks.index("TASK-002")
        assert result.ordered_tasks.index("TASK-002") < result.ordered_tasks.index("TASK-003")

    def test_detect_circular_dependency(self):
        tasks = [
            {"id": "TASK-001", "dependencies": ["TASK-002"], "estimated_hours": 1.0},
            {"id": "TASK-002", "dependencies": ["TASK-001"], "estimated_hours": 2.0},
        ]
        result = self.resolver.resolve(tasks)
        assert result.has_cycles

    def test_parallel_groups_identified(self):
        tasks = [
            {"id": "TASK-001", "dependencies": [], "estimated_hours": 1.0},
            {"id": "TASK-002", "dependencies": [], "estimated_hours": 2.0},
            {"id": "TASK-003", "dependencies": ["TASK-001", "TASK-002"], "estimated_hours": 3.0},
        ]
        result = self.resolver.resolve(tasks)
        assert len(result.parallel_groups) >= 1
        # First group should have TASK-001 and TASK-002
        first_group = result.parallel_groups[0]
        assert "TASK-001" in first_group
        assert "TASK-002" in first_group

    def test_critical_path_calculated(self):
        tasks = [
            {"id": "TASK-001", "dependencies": [], "estimated_hours": 1.0},
            {"id": "TASK-002", "dependencies": ["TASK-001"], "estimated_hours": 2.0},
            {"id": "TASK-003", "dependencies": [], "estimated_hours": 5.0},
        ]
        result = self.resolver.resolve(tasks)
        assert len(result.critical_path) > 0
        assert result.total_duration > 0

    def test_empty_tasks(self):
        result = self.resolver.resolve([])
        assert len(result.ordered_tasks) == 0
        assert not result.has_cycles

    def test_to_dict(self):
        tasks = [
            {"id": "TASK-001", "dependencies": [], "estimated_hours": 1.0},
        ]
        result = self.resolver.resolve(tasks)
        data = result.to_dict()
        assert 'ordered_tasks' in data
        assert 'parallel_groups' in data
        assert 'has_cycles' in data
