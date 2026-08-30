"""Tests for sandbox.py."""

import os
import tempfile

import pytest

from app.self_improvement.sandbox import SandboxBuilder


class TestSandboxBuilder:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.sandboxes_root = os.path.join(self.tmpdir, ".sandboxes")
        self.builder = SandboxBuilder(self.sandboxes_root)
        self.project_path = os.path.join(self.tmpdir, "project")
        os.makedirs(self.project_path)
        with open(os.path.join(self.project_path, "main.py"), "w") as f:
            f.write("def hello():\n    pass\n")

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_create_sandbox(self):
        sandbox = self.builder.create(self.project_path, "task-1")
        assert os.path.isdir(sandbox.sandbox_path)
        assert sandbox.status == "active"

    def test_apply_improvement(self):
        sandbox = self.builder.create(self.project_path, "task-1")
        new_content = "def hello():\n    print('improved')\n"
        result = self.builder.apply_improvement(sandbox.sandbox_id, "main.py", new_content)
        assert result is True

    def test_discard_sandbox(self):
        sandbox = self.builder.create(self.project_path, "task-1")
        self.builder.discard(sandbox.sandbox_id)
        assert not os.path.exists(sandbox.sandbox_path)

    def test_promote_sandbox(self):
        sandbox = self.builder.create(self.project_path, "task-1")
        new_content = "def hello():\n    print('improved')\n"
        self.builder.apply_improvement(sandbox.sandbox_id, "main.py", new_content)
        result = self.builder.promote(sandbox.sandbox_id, self.project_path)
        assert result is True

    def test_list_sandboxes(self):
        sandbox = self.builder.create(self.project_path, "task-1")
        sandboxes = self.builder.list_sandboxes()
        assert len(sandboxes) == 1
