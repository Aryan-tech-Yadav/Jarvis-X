"""Tests for project_state.py."""

import os
import tempfile

import pytest

from app.engineering.project_state import ProjectStateManager


class TestProjectStateManager:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.manager = ProjectStateManager(state_dir=self.tmpdir)

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_create_project(self):
        state = self.manager.create_project("proj-1", "Test Project", ["TASK-001", "TASK-002"])
        assert state.project_id == "proj-1"
        assert state.project_name == "Test Project"
        assert len(state.pending_tasks) == 2

    def test_complete_task(self):
        state = self.manager.create_project("proj-1", "Test", ["TASK-001"])
        self.manager.complete_task("proj-1", "TASK-001", ["file1.py"])
        state = self.manager.get_state("proj-1")
        assert "TASK-001" in state.completed_tasks
        assert "file1.py" in state.created_files

    def test_fail_task(self):
        state = self.manager.create_project("proj-1", "Test", ["TASK-001"])
        self.manager.fail_task("proj-1", "TASK-001", "Runtime error")
        state = self.manager.get_state("proj-1")
        assert "TASK-001" in state.failed_tasks
        assert len(state.runtime_errors) > 0

    def test_get_progress(self):
        state = self.manager.create_project("proj-1", "Test", ["TASK-001", "TASK-002"])
        self.manager.complete_task("proj-1", "TASK-001")
        progress = self.manager.get_progress("proj-1")
        assert progress["completed"] == 1
        assert progress["pending"] == 1
        assert progress["progress_percent"] == 50.0

    def test_update_coverage(self):
        state = self.manager.create_project("proj-1", "Test", [])
        self.manager.update_coverage("proj-1", 85.0)
        state = self.manager.get_state("proj-1")
        assert state.test_coverage == 85.0

    def test_set_phase(self):
        state = self.manager.create_project("proj-1", "Test", [])
        self.manager.set_phase("proj-1", "Phase 2 - Backend")
        state = self.manager.get_state("proj-1")
        assert state.current_phase == "Phase 2 - Backend"

    def test_state_persisted(self):
        self.manager.create_project("proj-1", "Test", ["TASK-001"])
        # Create new manager instance with same dir
        manager2 = ProjectStateManager(state_dir=self.tmpdir)
        state = manager2.get_state("proj-1")
        assert state is not None
        assert state.project_name == "Test"

    def test_to_dict(self):
        state = self.manager.create_project("proj-1", "Test", ["TASK-001"])
        data = state.to_dict()
        assert 'project_id' in data
        assert 'status' in data
        assert 'completed_tasks' in data
