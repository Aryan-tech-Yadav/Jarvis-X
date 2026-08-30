from time import time

from .models import JobState, RuntimeJob


class RuntimeScheduler:
    """FIFO scheduler with priority, delayed jobs, and bounded retries."""

    def __init__(self, clock=None):
        self.clock = clock or time
        self.jobs = {}
        self._pending = []
        self._sequence = 0

    def submit(self, job):
        if not isinstance(job, RuntimeJob):
            raise TypeError("RuntimeScheduler accepts RuntimeJob instances")
        if not callable(job.handler):
            raise ValueError("Runtime jobs require a callable handler")
        if job.job_id in self.jobs:
            raise ValueError("A job with this identifier already exists")
        job.not_before = max(float(job.not_before or 0.0), self.clock())
        self.jobs[job.job_id] = job
        self._enqueue(job)
        return job

    def next_job(self, now=None):
        now = self.clock() if now is None else float(now)
        ready = [item for item in self._pending if item[2].state == JobState.QUEUED and item[2].not_before <= now]
        if not ready:
            return None
        _, _, job = min(ready, key=lambda item: (item[0], item[1]))
        self._pending = [item for item in self._pending if item[2].job_id != job.job_id]
        job.state = JobState.RUNNING
        job.attempts += 1
        job.started_at = now
        return job

    def complete(self, job_id, result=None, now=None):
        job = self._require(job_id)
        job.state = JobState.COMPLETED
        job.result = result
        job.error = ""
        job.finished_at = self.clock() if now is None else float(now)
        return job

    def fail(self, job_id, error, now=None):
        job = self._require(job_id)
        job.error = str(error or "Job failed")
        moment = self.clock() if now is None else float(now)
        if job.attempts <= job.max_retries:
            job.state = JobState.QUEUED
            job.started_at = 0.0
            job.not_before = moment
            self._enqueue(job)
        else:
            job.state = JobState.FAILED
            job.finished_at = moment
        return job

    def cancel(self, job_id):
        job = self._require(job_id)
        if job.state != JobState.QUEUED:
            return False
        job.state = JobState.CANCELLED
        self._pending = [item for item in self._pending if item[2].job_id != job_id]
        return True

    def queued_count(self):
        return sum(job.state == JobState.QUEUED for job in self.jobs.values())

    def active_jobs(self):
        return [job for job in self.jobs.values() if job.state == JobState.RUNNING]

    def snapshot(self):
        return {"queued": self.queued_count(), "active": len(self.active_jobs()), "jobs": [job.snapshot() for job in self.jobs.values()]}

    def _enqueue(self, job):
        self._sequence += 1
        self._pending.append((-int(job.priority), self._sequence, job))

    def _require(self, job_id):
        try:
            return self.jobs[job_id]
        except KeyError as error:
            raise KeyError("Unknown runtime job: " + str(job_id)) from error
