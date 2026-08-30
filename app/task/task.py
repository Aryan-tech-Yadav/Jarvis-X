from dataclasses import dataclass, field
from time import time
from uuid import uuid4


@dataclass
class AutonomousTask:
    title: str
    task_id: str = field(default_factory=lambda: str(uuid4()))
    dependencies: list[str] = field(default_factory=list)
    priority: int = 0
    max_retries: int = 0
    eta_seconds: float = 0.0
    status: str = "pending"
    attempts: int = 0
    result: object = None
    created_at: float = field(default_factory=time)

    def can_retry(self):
        # ``max_retries=0`` explicitly disables retries, including when a task
        # fails before its first scheduler dispatch.
        return self.max_retries > 0 and self.attempts <= self.max_retries
