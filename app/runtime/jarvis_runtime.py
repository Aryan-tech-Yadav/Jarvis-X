from time import perf_counter, time

from app.core.results import ExecutionResult
from app.events.event_bus import EventBus
from app.metrics.metrics_manager import MetricsManager

from .models import RuntimeJob, RuntimeState
from .resource_monitor import ResourceMonitor
from .scheduler import RuntimeScheduler
from .snapshot_store import SnapshotStore
from .watchdog import RuntimeWatchdog


class JarvisRuntime:
    """Composition root for observable, bounded in-process runtime work."""

    def __init__(self, scheduler=None, events=None, metrics=None, resources=None, snapshots=None, clock=None):
        self.clock = clock or time
        self.scheduler = scheduler or RuntimeScheduler(clock=self.clock)
        self.events = events or EventBus()
        self.metrics = metrics or MetricsManager()
        self.resources = resources or ResourceMonitor()
        self.snapshots = snapshots or SnapshotStore()
        self.watchdog = RuntimeWatchdog(self.scheduler, self.clock)
        self.state = RuntimeState.NEW

    def initialize(self):
        if self.state == RuntimeState.STOPPED:
            return False
        self.state = RuntimeState.READY
        self.events.publish("RUNTIME_READY", {"state": self.state.value})
        return True

    def submit(self, name, handler, *, payload=None, priority=0, delay_seconds=0, max_retries=0, timeout_seconds=60):
        if self.state != RuntimeState.READY:
            raise RuntimeError("Runtime must be initialized before submitting jobs")
        job = RuntimeJob(name=name, handler=handler, payload=payload, priority=priority,
                         not_before=self.clock() + max(0.0, float(delay_seconds)),
                         max_retries=max(0, int(max_retries)), timeout_seconds=max(0.0, float(timeout_seconds)))
        self.scheduler.submit(job)
        self.events.publish("RUNTIME_JOB_QUEUED", {"job_id": job.job_id, "name": job.name})
        return job

    def run_next(self, now=None):
        if self.state != RuntimeState.READY:
            return ExecutionResult.failed("Runtime is not ready", status="unavailable")
        self.watchdog.check(now)
        job = self.scheduler.next_job(now)
        if job is None:
            return ExecutionResult.completed(message="No eligible runtime job", data={"idle": True})
        self.events.publish("RUNTIME_JOB_STARTED", {"job_id": job.job_id, "name": job.name, "attempt": job.attempts})
        started = perf_counter()
        result = ExecutionResult.timed(job.handler, job.payload)
        duration = perf_counter() - started
        self.metrics.record("runtime_jobs")
        self.metrics.record_runtime(duration)
        if result.success:
            self.scheduler.complete(job.job_id, result.to_dict(), now)
            self.events.publish("RUNTIME_JOB_COMPLETED", {"job_id": job.job_id, "duration": duration})
        else:
            self.metrics.record("failures")
            updated = self.scheduler.fail(job.job_id, result.message, now)
            self.events.publish("RUNTIME_JOB_FAILED", {"job_id": job.job_id, "retrying": updated.state.value == "queued"})
        return result

    def snapshot(self, label="runtime"):
        return self.snapshots.save({"state": self.state.value, "scheduler": self.scheduler.snapshot(),
                                    "metrics": self.metrics.export(), "resources": self.resources.sample()}, label)

    def health(self):
        resources = self.resources.sample()
        checks = {
            "state": self.state == RuntimeState.READY,
            "scheduler": self.scheduler is not None,
            "event_bus": self.events.alive(),
            "disk": resources["disk_free_bytes"] > 0,
        }
        return {"healthy": all(checks.values()), "state": self.state.value, "checks": checks,
                "queue": self.scheduler.snapshot(), "resources": resources, "metrics": self.metrics.export()}

    def shutdown(self):
        if self.state == RuntimeState.STOPPED:
            return True
        self.snapshot("shutdown")
        self.state = RuntimeState.STOPPED
        self.events.publish("RUNTIME_STOPPED", {"state": self.state.value})
        return True

    def restart(self):
        self.shutdown()
        self.state = RuntimeState.NEW
        return self.initialize()
