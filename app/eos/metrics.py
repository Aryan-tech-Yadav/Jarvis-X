from dataclasses import dataclass, field
from time import perf_counter
from typing import Any, Dict, List


@dataclass
class EOSMetrics:
    started_at: float = field(default_factory=perf_counter)
    duration_seconds: float = 0.0
    stages_completed: int = 0
    stages_failed: int = 0
    score: float = 0.0
    values: Dict[str, float] = field(default_factory=dict)
    executions: List[Dict[str, Any]] = field(default_factory=list)

    def finish(self) -> None:
        self.duration_seconds = perf_counter() - self.started_at

    def record_execution(self, **data: Any) -> None:
        self.executions.append(dict(data))
