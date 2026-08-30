"""Per-agent execution metrics."""

from dataclasses import dataclass


@dataclass
class AgentMetrics:
    executions: int = 0
    successes: int = 0
    failures: int = 0
    total_execution_time: float = 0.0

    def record(self, success: bool, duration: float) -> None:
        self.executions += 1
        self.successes += int(success)
        self.failures += int(not success)
        self.total_execution_time += max(0.0, duration)

    def snapshot(self) -> dict:
        return {
            "executions": self.executions,
            "successes": self.successes,
            "failures": self.failures,
            "total_execution_time": self.total_execution_time,
        }

