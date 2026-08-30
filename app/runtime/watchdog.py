from .models import JobState


class RuntimeWatchdog:
    def __init__(self, scheduler, clock):
        self.scheduler = scheduler
        self.clock = clock

    def check(self, now=None):
        now = self.clock() if now is None else float(now)
        timed_out = []
        for job in self.scheduler.active_jobs():
            if job.state == JobState.RUNNING and now - job.started_at > job.timeout_seconds:
                self.scheduler.fail(job.job_id, "Job exceeded timeout of {} seconds".format(job.timeout_seconds), now)
                timed_out.append(job.job_id)
        return timed_out
