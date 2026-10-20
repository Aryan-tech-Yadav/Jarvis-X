"""Tests for BackupManager, restore drills, and OperationalMetrics."""

import os
import tempfile
import unittest
from pathlib import Path

from app.diagnostics.backup_manager import BackupManager, OperationalMetrics


class TestOperationalMetrics(unittest.TestCase):
    def test_metrics_calculation(self):
        metrics = OperationalMetrics()
        self.assertEqual(metrics.success_rate, 100.0)
        self.assertEqual(metrics.failure_rate, 0.0)

        metrics.record_task(success=True, duration_sec=0.1)
        metrics.record_task(success=True, duration_sec=0.2, retried=True)
        metrics.record_task(success=False, duration_sec=0.3, timed_out=True)

        self.assertEqual(metrics.total_tasks, 3)
        self.assertEqual(metrics.successful_tasks, 2)
        self.assertEqual(metrics.failed_tasks, 1)
        self.assertEqual(metrics.retried_tasks, 1)
        self.assertEqual(metrics.timeout_tasks, 1)
        self.assertAlmostEqual(metrics.success_rate, 66.67, places=1)
        self.assertAlmostEqual(metrics.failure_rate, 33.33, places=1)
        self.assertAlmostEqual(metrics.retry_rate, 33.33, places=1)


class TestBackupManager(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tmpdir.name)
        self.source = self.root / "source"
        self.source.mkdir()
        (self.source / "data.json").write_text('{"key": "value"}', encoding="utf-8")
        (self.source / "sub").mkdir()
        (self.source / "sub" / "nested.txt").write_text("hello backup", encoding="utf-8")

        self.backup_mgr = BackupManager(backup_dir=self.root / "backups")

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_backup_and_restore(self):
        archive = self.backup_mgr.create_backup(self.source, tag="test")
        self.assertTrue(archive.is_file())

        target = self.root / "restored_dir"
        restored = self.backup_mgr.restore_backup(archive, target)
        self.assertTrue(restored)

        restored_file = target / "source" / "data.json"
        self.assertTrue(restored_file.is_file())
        self.assertEqual(restored_file.read_text(encoding="utf-8"), '{"key": "value"}')

    def test_restore_drill_passes(self):
        drill_result = self.backup_mgr.test_restore_drill(self.source)
        self.assertTrue(drill_result["success"])
        self.assertEqual(drill_result["files_checked"], 2)
        self.assertEqual(drill_result["missing_files"], [])

