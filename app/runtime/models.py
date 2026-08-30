from dataclasses import dataclass, field
from enum import Enum
from time import time
from uuid import uuid4


class RuntimeState(str, Enum):
    NEW = "new"
    READY = "ready"
    STOPPED = "stopped"
    FAILED = "failed"


class JobState(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class RuntimeJob:
    """A unit of runtime work.

    ``handler`` remains in-process only and is deliberately excluded from
    snapshots. Resuming a recovered snapshot requires the application to bind
    a handler again, avoiding accidental execution after a restart.
    """

    name: str
    handler: object
    payload: object = None
    priority: int = 0
    not_before: float = 0.0
    max_retries: int = 0
    timeout_seconds: float = 60.0
    job_id: str = field(default_factory=lambda: str(uuid4()))
    state: JobState = JobState.QUEUED
    attempts: int = 0
    result: object = None
    error: str = ""
    created_at: float = field(default_factory=time)
    started_at: float = 0.0
    finished_at: float = 0.0

    def snapshot(self):
        return {
            "job_id": self.job_id,
            "name": self.name,
            "payload": self.payload,
            "priority": self.priority,
            "not_before": self.not_before,
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds,
            "state": self.state.value,
            "attempts": self.attempts,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }
