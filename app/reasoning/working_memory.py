"""Bounded working memory for one reasoning task."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class WorkingMemory:
    """Explicit task context; bounded to prevent unreviewed context growth."""

    goal: str
    facts: List[str] = field(default_factory=list)
    unknowns: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    progress: List[str] = field(default_factory=list)
    confidence: float = 0.0
    max_items: int = 20

    def __post_init__(self) -> None:
        self.goal = self.goal.strip()
        if not self.goal:
            raise ValueError("Working memory requires a goal")
        self.confidence = max(0.0, min(1.0, float(self.confidence)))
        for name in ("facts", "unknowns", "constraints", "risks", "progress"):
            values = getattr(self, name)
            setattr(self, name, [str(item) for item in values[: self.max_items]])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal": self.goal,
            "facts": list(self.facts),
            "unknowns": list(self.unknowns),
            "constraints": list(self.constraints),
            "risks": list(self.risks),
            "progress": list(self.progress),
            "confidence": self.confidence,
        }


def build_working_memory(goal: str, context: Dict[str, Any] | None = None) -> WorkingMemory:
    """Build bounded memory from orchestrator context."""
    values = dict(context or {})
    return WorkingMemory(
        goal=goal,
        facts=list(values.get("known_facts", values.get("facts", []))),
        unknowns=list(values.get("unknowns", [])),
        constraints=list(values.get("constraints", [])),
        risks=list(values.get("risks", [])),
        confidence=values.get("confidence", 0.0),
    )
