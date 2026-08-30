"""Tests for orchestrator task_graph.py."""

import pytest

from app.orchestrator.task_graph import TaskGraph, TaskNode


class TestTaskGraph:
    def setup_method(self):
        self.graph = TaskGraph()

    def _make_task(self, task_id, dependencies=None, **kwargs):
        return TaskNode(
            id=task_id,
            title=f"Task {task_id}",
            description=f"Description for {task_id}",
            dependencies=dependencies or [],
            **kwargs,
        )

    def test_add_task(self):
        task = self._make_task("TASK-001")
        self.graph.add_task(task)
        assert self.graph.get_task("TASK-001") is not None

    def test_duplicate_task_raises(self):
        task1 = self._make_task("TASK-001")
        task2 = self._make_task("TASK-001")
        self.graph.add_task(task1)
        with pytest.raises(ValueError):
            self.graph.add_task(task2)

    def test_no_cycles(self):
        self.graph.add_task(self._make_task("A", dependencies=[]))
        self.graph.add_task(self._make_task("B", dependencies=["A"]))
        self.graph.add_task(self._make_task("C", dependencies=["B"]))
        assert len(self.graph.detect_cycles()) == 0

    def test_detect_cycle(self):
        self.graph.add_task(self._make_task("A", dependencies=["B"]))
        self.graph.add_task(self._make_task("B", dependencies=["A"]))
        assert len(self.graph.detect_cycles()) > 0

    def test_topological_sort(self):
        self.graph.add_task(self._make_task("A", dependencies=[]))
        self.graph.add_task(self._make_task("B", dependencies=["A"]))
        self.graph.add_task(self._make_task("C", dependencies=["B"]))
        order = self.graph.topological_sort()
        assert order.index("A") < order.index("B")
        assert order.index("B") < order.index("C")

    def test_parallel_groups(self):
        self.graph.add_task(self._make_task("A", dependencies=[]))
        self.graph.add_task(self._make_task("B", dependencies=[]))
        self.graph.add_task(self._make_task("C", dependencies=["A", "B"]))
        groups = self.graph.get_parallel_groups()
        assert len(groups) >= 2
        assert "A" in groups[0]
        assert "B" in groups[0]

    def test_get_ready_tasks(self):
        self.graph.add_task(self._make_task("A", dependencies=[], priority="high"))
        self.graph.add_task(self._make_task("B", dependencies=["A"]))
        ready = self.graph.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].id == "A"

    def test_critical_path(self):
        self.graph.add_task(self._make_task("A", dependencies=[], estimated_hours=1.0))
        self.graph.add_task(self._make_task("B", dependencies=["A"], estimated_hours=2.0))
        self.graph.add_task(self._make_task("C", dependencies=["A"], estimated_hours=5.0))
        path, duration = self.graph.get_critical_path()
        assert len(path) > 0
        assert duration > 0

    def test_mark_completed(self):
        self.graph.add_task(self._make_task("A"))
        self.graph.mark_completed("A")
        assert self.graph.get_task("A").status == "completed"

    def test_get_stats(self):
        self.graph.add_task(self._make_task("A"))
        self.graph.add_task(self._make_task("B", dependencies=["A"]))
        stats = self.graph.get_stats()
        assert stats["total_tasks"] == 2
        assert stats["total_dependencies"] == 1
