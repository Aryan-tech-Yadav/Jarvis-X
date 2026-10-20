"""Tests for FileManager atomic write, snapshot creation, and rollback."""

import os
import tempfile
import unittest
from pathlib import Path

from app.agent.file_manager import FileManager


class TestFileManagerSafety(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.fm = FileManager(workspace=self.tmpdir.name)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_atomic_save_and_read(self):
        path = self.fm.save_python("test_script.py", "print('atomic')")
        self.assertTrue(os.path.isfile(path))
        content = self.fm.read_file("test_script.py")
        self.assertEqual(content, "print('atomic')")

    def test_snapshot_and_rollback(self):
        # 1. Save original
        path = self.fm.save_python("module.py", "VERSION = 1")
        # 2. Overwrite with backup
        self.fm.overwrite_file("module.py", "VERSION = 2", create_backup=True)
        self.assertEqual(self.fm.read_file("module.py"), "VERSION = 2")
        self.assertTrue(Path(path).with_suffix(".py.bak").is_file())

        # 3. Rollback
        rolled_back = self.fm.rollback("module.py")
        self.assertTrue(rolled_back)
        self.assertEqual(self.fm.read_file("module.py"), "VERSION = 1")

    def test_rollback_returns_false_when_no_snapshot(self):
        self.fm.save_python("standalone.py", "x = 42")
        self.assertFalse(self.fm.rollback("standalone.py"))

