import unittest

from app.diagnostics.health_checker import HealthChecker
from app.runtime.jarvis_runtime import JarvisRuntime
from app.runtime.models import JobState, RuntimeJob, RuntimeState
from app.runtime.scheduler import RuntimeScheduler
from app.runtime.snapshot_store import SnapshotStore
from app.runtime.watchdog import RuntimeWatchdog


class RuntimeSchedulerTests(unittest.TestCase):
    def setUp(self):
        self.now = 100.0
        self.scheduler = RuntimeScheduler(clock=lambda: self.now)

    def test_priority_wins_and_equal_priority_remains_fifo(self):
        self.scheduler.submit(RuntimeJob("first", lambda _: True))
        self.scheduler.submit(RuntimeJob("high", lambda _: True, priority=3))
        self.scheduler.submit(RuntimeJob("second", lambda _: True))
        self.assertEqual(self.scheduler.next_job().name, "high")
        self.assertEqual(self.scheduler.next_job().name, "first")
        self.assertEqual(self.scheduler.next_job().name, "second")

    def test_delayed_job_is_not_available_early(self):
        self.scheduler.submit(RuntimeJob("later", lambda _: True, not_before=110))
        self.assertIsNone(self.scheduler.next_job())
        self.now = 110
        self.assertEqual(self.scheduler.next_job().name, "later")

    def test_failure_requeues_only_with_remaining_retry_budget(self):
        job = self.scheduler.submit(RuntimeJob("retry", lambda _: False, max_retries=1))
        self.scheduler.next_job()
        self.assertEqual(self.scheduler.fail(job.job_id, "temporary").state, JobState.QUEUED)
        self.scheduler.next_job()
        self.assertEqual(self.scheduler.fail(job.job_id, "permanent").state, JobState.FAILED)

    def test_snapshot_never_includes_handler(self):
        self.scheduler.submit(RuntimeJob("safe", lambda _: True))
        self.assertNotIn("handler", self.scheduler.snapshot()["jobs"][0])


class RuntimeKernelTests(unittest.TestCase):
    def setUp(self):
        self.now = 10.0
        self.runtime = JarvisRuntime(clock=lambda: self.now)
        self.runtime.initialize()

    def test_lifecycle_requires_initialization_and_supports_restart(self):
        runtime = JarvisRuntime()
        with self.assertRaises(RuntimeError):
            runtime.submit("blocked", lambda _: True)
        self.assertTrue(runtime.initialize())
        self.assertTrue(runtime.shutdown())
        self.assertEqual(runtime.state, RuntimeState.STOPPED)
        self.assertTrue(runtime.restart())
        self.assertEqual(runtime.state, RuntimeState.READY)

    def test_runtime_executes_job_records_event_and_metrics(self):
        job = self.runtime.submit("build", lambda payload: {"success": True, "value": payload}, payload="api")
        result = self.runtime.run_next(self.now)
        self.assertTrue(result.success)
        self.assertEqual(self.runtime.scheduler.jobs[job.job_id].state, JobState.COMPLETED)
        self.assertEqual(self.runtime.metrics.export()["runtime_jobs"], 1)
        self.assertEqual(self.runtime.events.history[-1].event_type, "RUNTIME_JOB_COMPLETED")

    def test_runtime_retries_failed_job_then_marks_it_failed(self):
        job = self.runtime.submit("flaky", lambda _: {"success": False, "message": "broken"}, max_retries=1)
        self.runtime.run_next(self.now)
        self.assertEqual(self.runtime.scheduler.jobs[job.job_id].state, JobState.QUEUED)
        self.runtime.run_next(self.now)
        self.assertEqual(self.runtime.scheduler.jobs[job.job_id].state, JobState.FAILED)

    def test_watchdog_recovers_expired_active_job(self):
        job = self.runtime.submit("slow", lambda _: True, timeout_seconds=2, max_retries=0)
        self.runtime.scheduler.next_job(self.now)
        self.assertEqual(self.runtime.watchdog.check(self.now + 3), [job.job_id])
        self.assertEqual(self.runtime.scheduler.jobs[job.job_id].state, JobState.FAILED)

    def test_runtime_snapshot_is_isolated(self):
        self.runtime.submit("build", lambda _: True, payload={"files": []})
        snapshot = self.runtime.snapshot()
        snapshot["payload"]["scheduler"]["jobs"][0]["payload"]["files"].append("mutated")
        saved = self.runtime.snapshots.get(snapshot["id"])
        self.assertEqual(saved["payload"]["scheduler"]["jobs"][0]["payload"]["files"], [])

    def test_health_checker_includes_runtime(self):
        result = HealthChecker(runtime=self.runtime).check()
        self.assertTrue(result["checks"]["runtime"])


class SnapshotStoreTests(unittest.TestCase):
    def test_latest_returns_copy_of_labeled_snapshot(self):
        store = SnapshotStore()
        store.save({"step": 1}, "build")
        item = store.save({"step": 2}, "build")
        self.assertEqual(store.latest("build")["id"], item["id"])


if __name__ == "__main__":
    unittest.main()
