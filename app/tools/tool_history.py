from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, List


@dataclass
class ToolCall:
    tool: str
    duration: float
    success: bool
    failure: str = ""
    changed_files: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ToolHistory:
    def __init__(self):
        self.calls = []

    def record(self, call):
        self.calls.append(call)

    def list(self):
        return list(self.calls)

    def statistics(self):
        values = {}
        for call in self.calls:
            name = call.tool if isinstance(call, ToolCall) else call.get("tool", "")
            success = call.success if isinstance(call, ToolCall) else bool(call.get("success"))
            if not name:
                continue
            item = values.setdefault(name, {"calls": 0, "successes": 0, "success_rate": 0.0})
            item["calls"] += 1
            item["successes"] += int(success)
            item["success_rate"] = item["successes"] / item["calls"]
        return values
