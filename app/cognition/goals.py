"""Goal stack with parent/child dependencies and lifecycle state."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4


class GoalStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Goal:
    description: str
    priority: int = 2
    deadline: Optional[str] = None
    risk: float = 0.0
    goal_id: str = field(default_factory=lambda: uuid4().hex)
    status: GoalStatus = GoalStatus.PENDING
    parent_id: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    children: List[str] = field(default_factory=list)
    progress: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {"goal_id": self.goal_id, "description": self.description,
                "priority": self.priority, "deadline": self.deadline, "risk": self.risk,
                "status": self.status.value, "parent_id": self.parent_id,
                "dependencies": list(self.dependencies), "children": list(self.children),
                "progress": self.progress}


class GoalStack:
    def __init__(self):
        self._goals: Dict[str, Goal] = {}

    def add(self, goal: Goal) -> Goal:
        if not goal.description.strip():
            raise ValueError("Goal description cannot be empty")
        if goal.parent_id:
            parent = self._goals.get(goal.parent_id)
            if parent is None:
                raise KeyError(f"Parent goal not found: {goal.parent_id}")
            parent.children.append(goal.goal_id)
        self._goals[goal.goal_id] = goal
        return goal

    def get(self, goal_id: str) -> Optional[Goal]:
        return self._goals.get(goal_id)

    def activate_next(self) -> Optional[Goal]:
        ready = [goal for goal in self._goals.values()
                 if goal.status == GoalStatus.PENDING
                 and all(self._goals.get(dep) and self._goals[dep].status == GoalStatus.COMPLETED
                         for dep in goal.dependencies)]
        if not ready:
            return None
        selected = max(ready, key=lambda goal: (goal.priority, -goal.risk))
        selected.status = GoalStatus.ACTIVE
        return selected

    def complete(self, goal_id: str, progress: float = 1.0) -> Goal:
        goal = self._require(goal_id)
        goal.status = GoalStatus.COMPLETED
        goal.progress = max(0.0, min(1.0, float(progress)))
        return goal

    def all(self) -> List[Goal]:
        return list(self._goals.values())

    def _require(self, goal_id: str) -> Goal:
        goal = self.get(goal_id)
        if goal is None:
            raise KeyError(f"Goal not found: {goal_id}")
        return goal

