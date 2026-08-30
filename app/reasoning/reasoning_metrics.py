from dataclasses import dataclass, field
from time import perf_counter


@dataclass
class ReasoningMetrics:
    iterations: int = 0
    tool_calls: int = 0
    failures: int = 0
    retries: int = 0
    time_taken: float = 0.0
    _started: float = field(default_factory=perf_counter, repr=False)

    def start(self):
        self._started = perf_counter()

    def finish(self):
        self.time_taken = perf_counter() - self._started

    def record(self, name, value=1):
        if name == "tool_calls":
            self.tool_calls += value
        elif name == "failures":
            self.failures += value
        elif name == "retries":
            self.retries += value

    def record_runtime(self, seconds):
        self.time_taken += float(seconds)

    @property
    def success_rate(self):
        return max(0.0, (self.tool_calls - self.failures) / self.tool_calls) if self.tool_calls else 0.0

    def to_dict(self):
        return {"iterations": self.iterations, "tools": self.tool_calls, "failures": self.failures,
                "retries": self.retries, "time_taken": self.time_taken, "success_rate": self.success_rate}