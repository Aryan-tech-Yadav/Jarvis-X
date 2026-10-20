from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ReasoningResult:
    goal: str
    success: bool
    iterations: int = 0
    steps: List[Dict[str, Any]] = field(default_factory=list)
    thoughts: List[Dict[str, Any]] = field(default_factory=list)
    observations: List[Dict[str, Any]] = field(default_factory=list)
    final_answer: str = ""
    status: str = "completed"
    message: str = ""
    history: List[Dict[str, Any]] = field(default_factory=list)
    completed: bool = False
    next_action: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {
            "goal": self.goal,
            "success": self.success,
            "iterations": self.iterations,
            "steps": self.steps,
            "thoughts": self.thoughts,
            "observations": self.observations,
            "final_answer": self.final_answer,
            "status": self.status,
            "message": self.message,
            "history": self.history,
            "completed": self.completed,
            "next_action": self.next_action,
            "metrics": self.metrics,
        }
