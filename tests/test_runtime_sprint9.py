"""Tests for Sprint 9 runtime modules."""

import json
import os
import tempfile
import unittest

from app.runtime.runtime_session import RuntimeSession, RuntimeSessionManager
from app.runtime.checkpoint_manager import CheckpointManager, Checkpoint
from app.runtime.retry_manager import RetryManager, RetryPolicy, RetryResult
from app.runtime.runtime_events import RuntimeEventBus, RuntimeEvent
from app.runtime.project_runtime import ProjectRuntime
from app.learning.project_history import ProjectHistory, ProjectHistoryEntry
from app.learning.improvement_engine import ImprovementEngine


class TestRuntimeSession(unittest.TestCase):
    def test_session_creation(self):
        session = RuntimeSession(project_name="Hospital", goal="Build Hospital Management System")
        self.assertEqual(session.project_name, "Hospital")
        self.assertEqual(session.goal, "Build Hospital Management System")
        self.assertTrue(session.session_id.startswith("session-"))

    def test_session_roundtrip(self):
        session = RuntimeSession(project_name="Hospital", goal="Build HMS", status="running")
        data = session.to_dict()
        restored = RuntimeSession.from_dict(data)
        self.assertEqual(restored.project_name, "Hospital")
        self.assertEqual(restored.status, "running")

    def test_session_manager_persists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = RuntimeSessionManager(sessions_dir=tmpdir)
            session = mgr.create_session("Hospital", "Build HMS", ["architect", "backend"])
            loaded = mgr.get_session(session.session_id)
            self.assertIsNotNone(loaded)
            self.assertEqual(loaded.project_name, "Hospital")
            self.assertEqual(len(loaded.pending_tasks), 2)

    def test_progress_tracking(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = RuntimeSessionManager(sessions_dir=tmpdir)
            session = mgr.create_session("Hospital", "Build HMS", ["architect", "backend"])
            mgr.complete_task(session.session_id, "architect")
            progress = mgr.get_progress(session.session_id)
            self.assertEqual(progress["completed"], 1)
            self.assertEqual(progress["pending"], 1)


class TestCheckpointManager(unittest.TestCase):
    def test_checkpoint_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = CheckpointManager(checkpoints_dir=tmpdir)
            ckpt = mgr.create_checkpoint("s1", "Hospital", "Build HMS",
                                         phase="backend",
                                         completed_tasks=["architect"],
                                         pending_tasks=["testing"])
            loaded = mgr.load(ckpt)
            self.assertIsNotNone(loaded)
            self.assertEqual(loaded.phase, "backend")
            self.assertEqual(loaded.completed_tasks, ["architect"])

    def test_latest_checkpoint(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = CheckpointManager(checkpoints_dir=tmpdir)
            mgr.create_checkpoint("s1", "Hospital", "Build HMS", phase="architect",
                                  completed_tasks=[], pending_tasks=[])
            mgr.create_checkpoint("s1", "Hospital", "Build HMS", phase="backend",
                                  completed_tasks=["architect"], pending_tasks=[])
            latest = mgr.latest("s1")
            self.assertEqual(latest.phase, "backend")

    def test_can_resume(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = CheckpointManager(checkpoints_dir=tmpdir)
            self.assertFalse(mgr.can_resume("s1"))
            mgr.create_checkpoint("s1", "Hospital", "Build HMS", phase="backend",
                                  completed_tasks=[], pending_tasks=[])
            self.assertTrue(mgr.can_resume("s1"))


class TestRetryManager(unittest.TestCase):
    def test_success_first_try(self):
        mgr = RetryManager()
        result = mgr.execute_with_retry("task", lambda: "ok")
        self.assertTrue(result.success)
        self.assertEqual(result.attempts, 1)

    def test_retry_then_success(self):
        calls = [0]
        def handler():
            calls[0] += 1
            if calls[0] < 3:
                raise RuntimeError("fail")
            return "ok"

        mgr = RetryManager(RetryPolicy(max_retries=3))
        result = mgr.execute_with_retry("task", handler)
        self.assertTrue(result.success)
        self.assertEqual(result.attempts, 3)

    def test_repair_handler_called(self):
        repairs = []
        def repair(err):
            repairs.append(str(err))

        def handler():
            raise RuntimeError("boom")

        mgr = RetryManager(RetryPolicy(max_retries=1))
        result = mgr.execute_with_retry("task", handler, repair_handler=repair)
        self.assertFalse(result.success)
        mgr.record("task", result)
        self.assertEqual(len(repairs), 1)

    def test_stats(self):
        mgr = RetryManager()
        r1 = mgr.execute_with_retry("task1", lambda: "ok")
        mgr.record("task1", r1)
        r2 = mgr.execute_with_retry("task2", lambda: (_ for _ in ()).throw(RuntimeError("x")))
        mgr.record("task2", r2)
        stats = mgr.stats()
        self.assertEqual(stats["total"], 2)
        self.assertEqual(stats["success_rate"], 0.5)


class TestRuntimeEvents(unittest.TestCase):
    def test_event_publish_and_persist(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "events.jsonl")
            bus = RuntimeEventBus(events_path=path)
            event = bus.publish("PHASE_STARTED", session_id="s1", phase="backend")
            self.assertEqual(event.event_type, "PHASE_STARTED")
            self.assertEqual(event.phase, "backend")

            history = bus.history(session_id="s1")
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0].phase, "backend")

    def test_event_filtering(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "events.jsonl")
            bus = RuntimeEventBus(events_path=path)
            bus.publish("PHASE_STARTED", session_id="s1", phase="backend")
            bus.publish("PHASE_COMPLETED", session_id="s1", phase="backend")
            bus.publish("PHASE_STARTED", session_id="s2", phase="frontend")

            history = bus.history(event_type="PHASE_STARTED")
            self.assertEqual(len(history), 2)


class TestProjectHistory(unittest.TestCase):
    def test_record_and_retrieve(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            history = ProjectHistory(history_path=os.path.join(tmpdir, "history.json"))
            entry = history.record_execution("Hospital", "Build HMS", "completed",
                                             120.5, overall_score=95.0)
            self.assertIsNotNone(entry)
            self.assertEqual(entry.project_name, "Hospital")

            similar = history.find_similar("Hospital Management", limit=2)
            self.assertEqual(len(similar), 1)
            self.assertEqual(similar[0].project_name, "Hospital")

    def test_stats(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            history = ProjectHistory(history_path=os.path.join(tmpdir, "history.json"))
            history.record_execution("Hospital", "Build HMS", "completed", 100.0)
            history.record_execution("Clinic", "Build Clinic", "failed", 50.0)
            stats = history.stats()
            self.assertEqual(stats["total"], 2)
            self.assertEqual(stats["success_rate"], 0.5)


class TestImprovementEngine(unittest.TestCase):
    def test_runtime_improvement(self):
        engine = ImprovementEngine()
        baseline = {"duration": 120.0, "repair_count": 5, "overall_score": 80.0}
        current = {"duration": 100.0, "repair_count": 3, "overall_score": 88.0}
        result = engine.compare(baseline, current)
        self.assertIn("duration_pct", result["deltas"])
        self.assertLess(result["deltas"]["duration_pct"], 0)
        self.assertLess(result["deltas"]["repair_count_delta"], 0)

    def test_no_change(self):
        engine = ImprovementEngine()
        result = engine.compare({"duration": 100.0}, {"duration": 100.0})
        self.assertEqual(result["deltas"], {})

    def test_notes_generated(self):
        engine = ImprovementEngine()
        baseline = {"repair_count": 10, "overall_score": 70.0}
        current = {"repair_count": 2, "overall_score": 90.0}
        result = engine.compare(baseline, current)
        self.assertTrue(len(result["notes"]) > 0)


class TestProjectRuntime(unittest.TestCase):
    def test_new_project_creates_session(self):
        runtime = ProjectRuntime()
        result = runtime.run("Build Test Project")
        self.assertIn("session_id", result)
        self.assertEqual(result["success"], True)

    def test_resume_without_checkpoint_raises(self):
        runtime = ProjectRuntime()
        with self.assertRaises(ValueError):
            runtime.run("Build Test Project", resume_session_id="missing-session")

    def test_improvement_engine_compare(self):
        engine = ImprovementEngine()
        baseline = {"duration": 120.0, "repair_count": 5}
        current = {"duration": 100.0, "repair_count": 3}
        result = engine.compare(baseline, current)
        self.assertIn("duration_pct", result["deltas"])
        self.assertIn("repair_count_delta", result["deltas"])


if __name__ == "__main__":
    unittest.main()
