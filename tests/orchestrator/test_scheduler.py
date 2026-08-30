"""Tests for orchestrator scheduler.py."""

import time

import pytest

from app.orchestrator.scheduler import ExecutionSchedule, TaskScheduler


class TestTaskScheduler:
    def setup_method(self):
        self.scheduler = TaskScheduler()

    def test_schedule_creates_phases(self):
        from app.orchestrator.task_graph import TaskGraph, TaskNode
        graph = TaskGraph()
        graph.add_task(TaskNode(id="A", title="A", description="d", agent="architect", dependencies=[]))
        graph.add_task(TaskNode(id="B", title="B", description="d", agent="backend", dependencies=["A"]))
        graph.add_task(TaskNode(id="C", title="C", description="d", agent="frontend", dependencies=["A"]))

        schedule = self.scheduler.schedule(graph)
        assert schedule.total_tasks == 3
        assert len(schedule.phases) >= 2

    def test_execute_runs_tasks(self):
        executed = []

        def executor(task):
            executed.append(task.task_id)
            return {"success": True}

        schedule = ExecutionSchedule(phases=[[
            type("t", (), {"task_id": "A", "agent": "architect", "priority": "high", "status": "pending", "result": None, "started_at": None, "completed_at": None, "error": None, "to_dict": lambda self: {}})()
        ]])
        schedule.total_tasks = 1
        result = self.scheduler.execute(schedule, executor)
        assert result.completed_tasks == 1
        assert "A" in executed

    def test_execute_handles_failures(self):
        def executor(task):
            return {"success": False, "error": "Test error"}

        schedule = ExecutionSchedule(phases=[[
            type("t", (), {"task_id": "A", "agent": "architect", "priority": "high", "status": "pending", "result": None, "started_at": None, "completed_at": None, "error": None, "to_dict": lambda self: {}})()
        ]])
        schedule.total_tasks = 1
        result = self.scheduler.execute(schedule, executor)
        assert result.failed_tasks == 1

    def test_stop_scheduler(self):
        self.scheduler.start_time = "2024-01-01T00:00:00"
        self.scheduler.stop()
        assert not self.scheduler.is_running
