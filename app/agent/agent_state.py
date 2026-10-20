from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List


@dataclass
class AgentState:
    goal: str
    status: str = "idle"
    iteration: int = 0
    tool_history: List[Dict[str, Any]] = field(default_factory=list)
    thought_history: List[Dict[str, Any]] = field(default_factory=list)
    observation_history: List[Dict[str, Any]] = field(default_factory=list)
    start_time: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def record(self, result: Dict[str, Any]):
        self.iteration = result.get("iterations", self.iteration)
        self.thought_history = result.get("thoughts", [])
        self.observation_history = result.get("observations", [])
        self.tool_history = [
            {"tool": thought.get("tool"), "action": thought.get("action"), "input": thought.get("input", {})}
            for thought in self.thought_history
        ]