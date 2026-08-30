import tempfile
import unittest

from app.events.event_bus import EventBus
from app.pipeline.generation_pipeline import GenerationPipeline
from app.workspace.workspace_manager import WorkspaceManager


class WorkspaceManagerTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.events = EventBus()
        self.manager = WorkspaceManager(self.directory.name, event_bus=self.events)
        self.manager.create_workspace()

    def tearDown(self):
        self.directory.cleanup()

    def test_projects_are_persisted_and_isolated(self):
        first = self.manager.create_project("Hospital Management")
        second = self.manager.create_project("Restaurant Management")
        first.memory["owner"] = "hospital"
        second.memory["owner"] = "restaurant"
        self.manager.save_project(first)
        self.manager.save_project(second)
        reopened = WorkspaceManager(self.directory.name)
        reopened.load_workspace()
        self.assertEqual(reopened.open_project(first.project_id).memory["owner"], "hospital")
        self.assertEqual(reopened.open_project(second.project_id).memory["owner"], "restaurant")

    def test_open_switches_active_project_and_publishes_events(self):
        first = self.manager.create_project("First")
        second = self.manager.create_project("Second")
        self.manager.open_project(first.project_id)
        self.manager.open_project(second.project_id)
        self.assertEqual(self.manager.registry.active_project_id, second.project_id)
        self.assertIn("PROJECT_OPENED", [event.event_type for event in self.events.history])

    def test_snapshot_restores_project_state(self):
        project = self.manager.create_project("Notes")
        project.memory["version"] = 1
        self.manager.save_project(project)
        snapshot = self.manager.snapshot_project(project.project_id)
        project.memory["version"] = 2
        self.manager.save_project(project)
        restored = self.manager.restore_snapshot(project.project_id, snapshot)
        self.assertEqual(restored.memory["version"], 1)

    def test_archive_restore_and_delete_are_recoverable(self):
        project = self.manager.create_project("CRM")
        archived = self.manager.archive_project(project.project_id)
        self.assertEqual(archived.metadata.location, "archive")
        restored = self.manager.restore_project(project.project_id)
        self.assertEqual(restored.metadata.location, "active")
        deleted = self.manager.delete_project(project.project_id)
        self.assertEqual(deleted.metadata.location, "trash")
        self.assertEqual(self.manager.list_projects(), [])
        self.assertEqual(self.manager.restore_project(project.project_id).metadata.location, "active")

    def test_metrics_aggregate_project_outcomes(self):
        complete = self.manager.create_project("Complete")
        complete.touch("completed")
        complete.metrics.update({"runtime_seconds": 4, "repair_count": 2, "benchmarks": 1})
        self.manager.save_project(complete)
        failed = self.manager.create_project("Failed")
        failed.touch("failed")
        failed.metrics["runtime_seconds"] = 2
        self.manager.save_project(failed)
        report = self.manager.metrics()
        self.assertEqual(report["completed"], 1)
        self.assertEqual(report["failed"], 1)
        self.assertEqual(report["average_runtime_seconds"], 3)

    def test_workspace_pipeline_snapshots_and_persists_result(self):
        project = self.manager.create_project("Notes API", "Build a web notes app with search")
        result = self.manager.run_pipeline(project.project_id, GenerationPipeline())
        reloaded = self.manager.open_project(project.project_id)
        self.assertTrue(result.success)
        self.assertEqual(reloaded.status, "completed")
        self.assertIn("snapshot_id", reloaded.executor_state)
        self.assertTrue(reloaded.reports)

    def test_unknown_project_and_missing_workspace_are_rejected(self):
        with self.assertRaises(KeyError):
            self.manager.open_project("missing")
        missing = WorkspaceManager(self.directory.name + "-missing")
        with self.assertRaises(FileNotFoundError):
            missing.load_workspace()


class WorkspaceCliTests(unittest.TestCase):
    def test_cli_creates_project_lists_and_reports_workspace_health(self):
        from app.release import cli

        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(cli.main(["workspace", "create", directory]), 0)
            self.assertEqual(cli.main(["workspace", "project-create", directory, "Notes"]), 0)
            self.assertEqual(cli.main(["workspace", "list", directory]), 0)
            self.assertEqual(cli.main(["workspace", "doctor", directory]), 0)


if __name__ == "__main__":
    unittest.main()
