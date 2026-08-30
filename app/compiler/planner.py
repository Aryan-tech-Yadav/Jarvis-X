"""Compile an engineering specification into an EOS-ready workflow plan."""

from dataclasses import dataclass, field
from typing import Dict, List

from .parser import EngineeringSpec


@dataclass
class WorkflowPlan:
    project: str
    steps: List[Dict[str, object]] = field(default_factory=list)

    def to_dict(self):
        return {"project": self.project, "steps": [dict(step) for step in self.steps]}


class WorkflowPlanner:
    def plan(self, spec: EngineeringSpec) -> WorkflowPlan:
        steps = [
            {"id": "requirements", "stage": "requirements", "depends_on": []},
            {"id": "architecture", "stage": "architecture", "depends_on": ["requirements"]},
            {"id": "implementation", "stage": "implementation", "depends_on": ["architecture"],
             "modules": list(spec.modules)},
            {"id": "verification", "stage": "verification", "depends_on": ["implementation"]},
        ]
        return WorkflowPlan(spec.project, steps)

