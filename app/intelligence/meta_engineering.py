"""Meta-engineering contracts for uncertainty, review, and safe improvement."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping

from app.memory.memory_compressor import MemoryCompressor
from app.quality.root_cause_engine import RootCauseEngine
from app.self_improvement.risk_engine import RiskEngine


@dataclass(frozen=True)
class UncertaintyAssessment:
    """Evidence-based confidence and next action."""

    known_facts: tuple[str, ...]
    unknowns: tuple[str, ...]
    assumptions: tuple[str, ...]
    risk_score: float
    confidence: float
    action: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "known_facts": list(self.known_facts),
            "unknowns": list(self.unknowns),
            "assumptions": list(self.assumptions),
            "risk_score": self.risk_score,
            "confidence": self.confidence,
            "action": self.action,
        }


@dataclass(frozen=True)
class MetaCognitionReview:
    """Review of whether a proposed reasoning path is trustworthy."""

    understood: bool
    assumption_count: int
    alternative_count: int
    overconfident: bool
    research_required: bool
    ask_user: bool
    repeated_mistake: bool
    reasons: tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "understood": self.understood,
            "assumption_count": self.assumption_count,
            "alternative_count": self.alternative_count,
            "overconfident": self.overconfident,
            "research_required": self.research_required,
            "ask_user": self.ask_user,
            "repeated_mistake": self.repeated_mistake,
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True)
class ImprovementProposal:
    """A non-mutating repair/refactoring proposal awaiting gated execution."""

    kind: str
    target: str
    diagnosis: Dict[str, Any]
    risk: Dict[str, Any]
    verification: tuple[str, ...]
    requires_approval: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "target": self.target,
            "diagnosis": dict(self.diagnosis),
            "risk": dict(self.risk),
            "verification": list(self.verification),
            "requires_approval": self.requires_approval,
        }


class MetaEngineeringEngine:
    """Coordinate meta-cognition without executing or mutating project code."""

    def __init__(
        self,
        *,
        root_cause: RootCauseEngine | None = None,
        risk_engine: RiskEngine | None = None,
        compressor: MemoryCompressor | None = None,
    ) -> None:
        self.root_cause = root_cause or RootCauseEngine()
        self.risk_engine = risk_engine or RiskEngine()
        self.compressor = compressor or MemoryCompressor()

    def assess_uncertainty(self, evidence: Mapping[str, Any]) -> UncertaintyAssessment:
        if not isinstance(evidence, Mapping):
            raise TypeError("Uncertainty evidence must be a mapping")
        known = self._strings(evidence.get("known_facts", ()))
        unknowns = self._strings(evidence.get("unknowns", ()))
        assumptions = self._strings(evidence.get("assumptions", ()))
        risk = self._bounded(evidence.get("risk_score", 0.0))
        confidence = 0.7 + min(0.2, len(known) * 0.05)
        confidence -= min(0.3, len(unknowns) * 0.1)
        confidence -= min(0.2, risk / 500.0)
        confidence = self._bounded(confidence, scale=1.0)
        if confidence >= 0.8 and risk < 30:
            action = "answer"
        elif confidence >= 0.5:
            action = "ask_user"
        else:
            action = "research"
        return UncertaintyAssessment(
            tuple(known), tuple(unknowns), tuple(assumptions),
            round(risk, 2), round(confidence, 4), action,
        )

    def review_thinking(self, context: Mapping[str, Any]) -> MetaCognitionReview:
        if not isinstance(context, Mapping):
            raise TypeError("Meta-cognition context must be a mapping")
        assumptions = self._strings(context.get("assumptions", ()))
        alternatives = self._strings(context.get("alternatives", ()))
        confidence = float(context.get("confidence", 0.0))
        risks = self._strings(context.get("risks", ()))
        repeated = bool(context.get("repeated_mistake"))
        reasons: List[str] = []
        overconfident = confidence >= 0.9 and (assumptions or risks)
        if overconfident:
            reasons.append("Confidence is high despite unresolved assumptions or risks")
        if not alternatives:
            reasons.append("No alternative reasoning path was recorded")
        if repeated:
            reasons.append("Context matches a previously observed mistake")
        return MetaCognitionReview(
            understood=bool(str(context.get("goal", "")).strip()),
            assumption_count=len(assumptions),
            alternative_count=len(alternatives),
            overconfident=overconfident,
            research_required=not bool(context.get("facts_verified", False)),
            ask_user=not bool(str(context.get("goal", "")).strip()) or bool(context.get("needs_clarification")),
            repeated_mistake=repeated,
            reasons=tuple(reasons),
        )

    def propose_debug_repair(
        self,
        failure_message: str,
        *,
        raw_traceback: str = "",
        context_code: str | None = None,
        target: str = "",
    ) -> ImprovementProposal:
        diagnosis = self.root_cause.diagnose(
            failure_message, raw_traceback=raw_traceback, context_code=context_code
        )
        task = {
            "id": f"repair:{diagnosis.error_category}",
            "type": "bug",
            "risk": "high" if diagnosis.confidence < 0.9 else "medium",
            "effort": "medium",
            "file": target or (diagnosis.target_files[0] if diagnosis.target_files else ""),
        }
        risk = self.risk_engine.assess(task, context_code or "").to_dict()
        return ImprovementProposal(
            kind="debug_repair",
            target=target or (diagnosis.target_files[0] if diagnosis.target_files else ""),
            diagnosis=diagnosis.to_dict(),
            risk=risk,
            verification=tuple(risk["suggested_tests"]),
            requires_approval=bool(risk["requires_approval"]),
        )

    def compress_experiences(self, entries: Iterable[Any]) -> Dict[str, Any]:
        """Return a bounded representation; callers decide when to persist it."""
        return self.compressor.compress(entries)

    @staticmethod
    def _strings(values: Any) -> List[str]:
        if isinstance(values, str):
            return [values]
        return [str(value) for value in (values or ())]

    @staticmethod
    def _bounded(value: Any, scale: float = 100.0) -> float:
        return max(0.0, min(scale, float(value)))
