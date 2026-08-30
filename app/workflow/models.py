from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Tuple
from uuid import uuid4


class WorkflowStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowStepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass
class WorkflowStep:
    step_id: str
    name: str
    depends_on: Tuple[str, ...] = field(default_factory=tuple)
    required: bool = True
    when: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: WorkflowStepStatus = WorkflowStepStatus.PENDING

    def __post_init__(self):
        self.step_id = self._clean(self.step_id, "step_id")
        self.name = self._clean(self.name, "name")
        self.depends_on = tuple(self._clean(value, "dependency") for value in self.depends_on)
        if not isinstance(self.required, bool):
            raise ValueError("required must be a boolean")
        if not isinstance(self.when, str):
            raise ValueError("when must be a string")
        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be a dictionary")

    @staticmethod
    def _clean(value, field_name):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be a non-empty string")
        return value.strip()

    def to_dict(self):
        return {
            "id": self.step_id,
            "name": self.name,
            "depends_on": list(self.depends_on),
            "required": self.required,
            "when": self.when,
            "metadata": dict(self.metadata),
            "status": self.status.value,
        }


@dataclass
class Workflow:
    goal: str
    steps: List[WorkflowStep]
    workflow_id: str = field(default_factory=lambda: str(uuid4()))
    status: WorkflowStatus = WorkflowStatus.DRAFT
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.goal, str) or not self.goal.strip():
            raise ValueError("goal must be a non-empty string")
        self.goal = self.goal.strip()
        if not isinstance(self.steps, list) or not self.steps:
            raise ValueError("workflow must contain at least one step")
        if not all(isinstance(step, WorkflowStep) for step in self.steps):
            raise TypeError("steps must be WorkflowStep instances")
        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be a dictionary")

    def step(self, step_id):
        return next((step for step in self.steps if step.step_id == step_id), None)

    def to_dict(self):
        return {
            "id": self.workflow_id,
            "goal": self.goal,
            "status": self.status.value,
            "steps": [step.to_dict() for step in self.steps],
            "metadata": dict(self.metadata),
        }
