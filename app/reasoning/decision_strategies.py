"""Reusable, explainable technology decision strategies."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DecisionStrategy:
    decision: str
    reason: str
    confidence: float
    matches: tuple[str, ...] = ()

    def applies(self, requirements: dict) -> bool:
        text = str(requirements).casefold()
        return not self.matches or any(match in text for match in self.matches)
