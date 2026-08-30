"""Tests for version_manager.py."""

import os
import tempfile

import pytest

from app.self_improvement.version_manager import VersionManager, ProjectVersion


class TestVersionManager:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.versions_root = os.path.join(self.tmpdir, ".versions")
        self.project_path = os.path.join(self.tmpdir, "project")
        os.makedirs(self.project_path)
        with open(os.path.join(self.project_path, "main.py"), "w") as f:
            f.write("def hello():\n    pass\n")
        self.manager = VersionManager(self.versions_root)

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_create_version(self):
        version = self.manager.create_version(self.project_path, score=85.0)
        assert isinstance(version, ProjectVersion)
        assert version.score == 85.0
        assert os.path.isdir(version.snapshot_path)

    def test_list_versions(self):
        self.manager.create_version(self.project_path)
        versions = self.manager.list_versions()
        assert len(versions) == 1

    def test_get_version(self):
        version = self.manager.create_version(self.project_path)
        fetched = self.manager.get_version(version.version_id)
        assert fetched is not None
        assert fetched.version_id == version.version_id

    def test_get_latest_version(self):
        v1 = self.manager.create_version(self.project_path, version_name="v1")
        v2 = self.manager.create_version(self.project_path, version_name="v2")
        latest = self.manager.get_latest_version()
        assert latest.version_id == v2.version_id

    def test_delete_version(self):
        version = self.manager.create_version(self.project_path)
        result = self.manager.delete(version.version_id)
        assert result is True
        assert self.manager.get_version(version.version_id) is None
