from dataclasses import dataclass


@dataclass
class Decision:
    tool: str
    reason: str
    confidence: float = 0.0
    priority: str = "NORMAL"

    def to_dict(self):
        return {"tool": self.tool, "reason": self.reason, "confidence": self.confidence, "priority": self.priority}