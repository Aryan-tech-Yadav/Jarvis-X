"""Plan critique contract."""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .planner import Plan


@dataclass
class Critique:
    approved: bool
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    confidence: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        return {"approved": self.approved, "issues": list(self.issues),
                "suggestions": list(self.suggestions), "confidence": self.confidence}


class Critic:
    def review(self, plan: Plan, context: Dict[str, Any] | None = None) -> Critique:
        issues = ["Plan has no executable steps"] if not plan.steps else []
        return Critique(not issues, issues=issues, confidence=0.9 if not issues else 0.2)

