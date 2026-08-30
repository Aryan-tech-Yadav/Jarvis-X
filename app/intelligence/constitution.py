"""Immutable engineering principles and confidence-aware decision validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Mapping


@dataclass(frozen=True)
class Principle:
    """An immutable engineering principle."""

    identifier: str
    statement: str
    check: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "id": self.identifier,
            "statement": self.statement,
            "check": self.check,
        }


DEFAULT_PRINCIPLES = (
    Principle("P001", "Never duplicate business logic.", "duplication"),
    Principle("P002", "Always validate before changing or refactoring.", "validation"),
    Principle("P003", "Never expose secrets.", "secrets"),
    Principle("P004", "Always validate external input.", "input_validation"),
    Principle("P005", "Prefer composition over inheritance.", "composition"),
    Principle("P006", "Never deploy code that fails mandatory quality gates.", "quality_gate"),
    Principle("P007", "When confidence is low, ask instead of guessing.", "confidence"),
)


@dataclass(frozen=True)
class ConstitutionDecision:
    """Decision outcome after constitutional and confidence checks."""

    action: str
    confidence: float
    approved: bool
    reasons: tuple[str, ...] = ()
    principles: tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "confidence": self.confidence,
            "approved": self.approved,
            "reasons": list(self.reasons),
            "principles": list(self.principles),
        }


class EngineeringConstitution:
    """Stable decision boundary that self-improving components cannot mutate."""

    def __init__(self, principles: Iterable[Principle] = DEFAULT_PRINCIPLES):
        values = tuple(principles)
        if not values or len({item.identifier for item in values}) != len(values):
            raise ValueError("Constitution requires unique, non-empty principles")
        self._principles = values

    @property
    def principles(self) -> tuple[Principle, ...]:
        return self._principles

    def validate(
        self,
        decision: Mapping[str, Any],
        *,
        confidence: float,
        evidence: Mapping[str, Any] | None = None,
    ) -> ConstitutionDecision:
        """Validate an intended action without executing it."""
        if not isinstance(decision, Mapping):
            raise TypeError("Decision must be a mapping")
        value = max(0.0, min(1.0, float(confidence)))
        context = dict(evidence or {})
        action = str(decision.get("action", decision.get("tool", ""))).strip()
        reasons: list[str] = []
        matched: list[str] = []

        if not action:
            reasons.append("Decision has no action")
        if value < 0.8:
            reasons.append("Confidence is below the automatic execution threshold")
            matched.append("P007")
        if context.get("known_mistake"):
            reasons.append("Decision matches a known engineering mistake")
            matched.append("P002")
        if context.get("secrets_detected"):
            reasons.append("Potential secrets detected")
            matched.append("P003")
        if context.get("quality_gate_passed") is False:
            reasons.append("Mandatory quality gate has not passed")
            matched.append("P006")
        if context.get("external_input") and not context.get("input_validated"):
            reasons.append("External input is not validated")
            matched.append("P004")

        return ConstitutionDecision(
            action=action,
            confidence=round(value, 4),
            approved=not reasons,
            reasons=tuple(reasons),
            principles=tuple(dict.fromkeys(matched)),
        )


class ConfidenceEngine:
    """Compute bounded confidence from evidence, uncertainty, and risk signals."""

    def evaluate(self, evidence: Mapping[str, Any]) -> float:
        if not isinstance(evidence, Mapping):
            raise TypeError("Confidence evidence must be a mapping")
        score = float(evidence.get("base", 0.5))
        score += min(0.3, 0.1 * len(evidence.get("validated_facts", ())))
        score -= min(0.3, 0.1 * len(evidence.get("uncertainties", ())))
        if evidence.get("high_risk"):
            score -= 0.2
        if evidence.get("quality_gate_passed") is True:
            score += 0.1
        return round(max(0.0, min(1.0, score)), 4)

    def route(self, confidence: float) -> str:
        value = max(0.0, min(1.0, float(confidence)))
        if value >= 0.95:
            return "execute"
        if value >= 0.8:
            return "reflect"
        if value >= 0.6:
            return "critic"
        if value >= 0.4:
            return "ask_user"
        return "stop"
