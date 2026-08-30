from dataclasses import dataclass, field


@dataclass(frozen=True)
class StrategyResult:
    """A ranked, explainable implementation approach."""

    name: str
    description: str
    score: float
    confidence: float
    difficulty: str
    estimated_minutes: int
    risk: float
    reasons: tuple = field(default_factory=tuple)

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "score": self.score,
            "confidence": self.confidence,
            "difficulty": self.difficulty,
            "estimated_minutes": self.estimated_minutes,
            "risk": self.risk,
            "reasons": list(self.reasons),
        }
