"""Replaceable planning contract for the reasoning layer."""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Plan:
    goal: str
    steps: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"goal": self.goal, "steps": list(self.steps),
                "assumptions": list(self.assumptions), "risks": list(self.risks)}


class Planner:
    """Build a conservative plan from a goal; providers may subclass this."""

    def create(self, goal: str, context: Dict[str, Any] | None = None) -> Plan:
        objective = str(goal).strip()
        if not objective:
            raise ValueError("Goal cannot be empty")
        return Plan(objective, steps=[f"Understand: {objective}", "Validate the proposed approach",
                                     "Execute the validated plan"])

