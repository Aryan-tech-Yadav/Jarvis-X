"""Deterministic cognitive routing decisions, separate from execution."""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class CognitiveDecision:
    action: str
    reason: str
    confidence: float
    alternatives: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"action": self.action, "reason": self.reason,
                "confidence": self.confidence, "alternatives": list(self.alternatives)}


class CognitiveDecisionEngine:
    def decide(self, goal: str, context: Dict[str, Any] | None = None) -> CognitiveDecision:
        if not isinstance(goal, str) or not goal.strip():
            raise ValueError("Goal cannot be empty")
        values = dict(context or {})
        text = goal.casefold()
        if values.get("needs_clarification") or "unclear" in text:
            return CognitiveDecision("ask_user", "Required information is missing", 0.95,
                                     ["research", "plan"])
        if values.get("high_risk") or any(word in text for word in ("delete", "deploy", "production")):
            return CognitiveDecision("ask_user", "The requested operation is high risk", 0.9,
                                     ["simulate", "execute"])
        if values.get("research") or "research" in text or "compare" in text:
            return CognitiveDecision("research", "Goal requires evidence before execution", 0.85,
                                     ["plan", "ask_user"])
        return CognitiveDecision("plan", "Goal is actionable and should be planned first", 0.8,
                                 ["research", "ask_user"])

