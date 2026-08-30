"""Tool metrics and telemetry collection."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ToolExecutionMetric:
    tool_name: str
    total_calls: int = 0
    success_count: int = 0
    failure_count: int = 0
    total_duration_sec: float = 0.0
    retries_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        avg = (self.total_duration_sec / max(1, self.total_calls)) if self.total_calls > 0 else 0.0
        rate = (self.success_count / max(1, self.total_calls)) * 100.0 if self.total_calls > 0 else 100.0
        return {
            "tool_name": self.tool_name,
            "total_calls": self.total_calls,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate_pct": round(rate, 2),
            "average_duration_sec": round(avg, 4),
            "total_duration_sec": round(self.total_duration_sec, 3),
            "retries_count": self.retries_count,
        }


class ToolMetricsTracker:
    """Collects runtime performance, success rates, and retries per tool."""

    def __init__(self):
        self._metrics: Dict[str, ToolExecutionMetric] = defaultdict(lambda: ToolExecutionMetric(""))

    def record_call(self, tool_name: str, success: bool, duration_sec: float, retries: int = 0):
        m = self._metrics[tool_name]
        m.tool_name = tool_name
        m.total_calls += 1
        if success:
            m.success_count += 1
        else:
            m.failure_count += 1
        m.total_duration_sec += duration_sec
        m.retries_count += retries

    def get_summary(self) -> Dict[str, Any]:
        return {name: m.to_dict() for name, m in self._metrics.items()}
