from typing import Any, Protocol


class Scheduler(Protocol):
    def submit(self, job: Any) -> Any:
        ...

    def next_job(self, now: Any = None) -> Any:
        ...
