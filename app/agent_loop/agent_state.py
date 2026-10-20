from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class AgentState:
    goal: str = ""
    plan: List[str] = field(default_factory=list)
    current_step: int = 0
    history: List[Dict[str, Any]] = field(default_factory=list)
    finished: bool = False

    def next_step(self):
        self.current_step += 1
        return self.current_step

    def complete_step(self):
        return self.current_step

    def add_observation(self, thought, action, observation):
        self.history.append({"thought": thought, "action": action, "observation": observation})

    def is_finished(self):
        return self.finished

    def to_dict(self):
        return {"goal": self.goal, "plan": self.plan, "current_step": self.current_step,
                "history": self.history, "finished": self.finished}

    @classmethod
    def from_dict(cls, data):
        return cls(goal=data.get("goal", ""), plan=list(data.get("plan", [])),
                   current_step=data.get("current_step", 0), history=list(data.get("history", [])),
                   finished=bool(data.get("finished", False)))