from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List


@dataclass
class Task:
    goal: str
    current_step: str = "planner"
    status: str = "pending"
    result: Any = None
    history: List[Dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_steps: List[str] = field(default_factory=list)
    memory_snapshot: Dict[str, Any] = field(default_factory=dict)
    reasoning_trace: List[Dict[str, Any]] = field(default_factory=list)

    def record(self, agent: str, result: Any):
        self.current_step = agent
        self.result = result
        self.history.append({"agent": agent, "result": result})
        if agent not in self.completed_steps:
            self.completed_steps.append(agent)
        if agent == "reasoning" and isinstance(result, dict):
            self.reasoning_trace = result.get("history", [])

    def to_dict(self):
        return {
            "goal": self.goal,
            "current_step": self.current_step,
            "status": self.status,
            "result": self.result,
            "history": self.history,
            "created_at": self.created_at,
            "completed_steps": self.completed_steps,
            "memory_snapshot": self.memory_snapshot,
            "reasoning_trace": self.reasoning_trace,
        }