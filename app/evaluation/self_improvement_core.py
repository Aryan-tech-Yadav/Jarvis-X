"""Safe, measurable Self Improvement Core (SIC)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional

from app.intelligence.meta_engineering import MetaEngineeringEngine
from app.quality.lifecycle_gate import LifecycleQualityGate

from .autonomous_improvement import AutonomousImprovementEngine
from .maturity import EngineeringMaturityEngine


@dataclass(frozen=True)
class SelfObservation:
    """Immutable evidence captured after a task."""

    task_id: str
    outcome: str
    metrics: Dict[str, Any] = field(default_factory=dict)
    failures: tuple[str, ...] = ()
    observed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "outcome": self.outcome,
            "metrics": dict(self.metrics),
            "failures": list(self.failures),
            "observed_at": self.observed_at,
        }


@dataclass(frozen=True)
class SICReport:
    """Auditable result of one self-improvement cycle."""

    observation: SelfObservation
    critique: Dict[str, Any]
    proposals: List[Dict[str, Any]]
    experiment: Dict[str, Any]
    decision: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "observation": self.observation.to_dict(),
            "critique": dict(self.critique),
            "proposals": [dict(item) for item in self.proposals],
            "experiment": dict(self.experiment),
            "decision": self.decision,
        }


class SelfImprovementCore:
    """Coordinate observation through evolution without direct self-modification."""

    def __init__(
        self,
        *,
        meta_engine: Optional[MetaEngineeringEngine] = None,
        maturity_engine: Optional[EngineeringMaturityEngine] = None,
        lifecycle_gate: Optional[LifecycleQualityGate] = None,
        improvement_engine: Optional[AutonomousImprovementEngine] = None,
    ) -> None:
        self.meta = meta_engine or MetaEngineeringEngine()
        self.maturity = maturity_engine or EngineeringMaturityEngine()
        self.lifecycle_gate = lifecycle_gate or LifecycleQualityGate()
        self.improvement = improvement_engine
        self._observations: List[SelfObservation] = []

    def observe(
        self,
        task_id: str,
        *,
        outcome: str,
        metrics: Optional[Mapping[str, Any]] = None,
        failures: Optional[Iterable[str]] = None,
    ) -> SelfObservation:
        if not str(task_id).strip():
            raise ValueError("SIC observation requires task_id")
        observation = SelfObservation(
            task_id=str(task_id).strip(),
            outcome=str(outcome).strip().upper(),
            metrics=dict(metrics or {}),
            failures=tuple(str(item) for item in (failures or ())),
        )
        self._observations.append(observation)
        return observation

    def analyze(self, observation: SelfObservation) -> Dict[str, Any]:
        """Critique the process and identify evidence-backed weaknesses."""
        if not isinstance(observation, SelfObservation):
            raise TypeError("analyze requires a SelfObservation")
        confidence = float(observation.metrics.get("confidence", 0.5))
        critique = self.meta.review_thinking({
            "goal": observation.task_id,
            "confidence": confidence,
            "assumptions": observation.metrics.get("assumptions", ()),
            "alternatives": observation.metrics.get("alternatives", ()),
            "risks": observation.metrics.get("risks", ()),
            "facts_verified": observation.metrics.get("facts_verified", False),
            "repeated_mistake": observation.metrics.get("repeated_mistake", False),
        })
        return critique.to_dict()

    def cycle(
        self,
        observation: SelfObservation,
        *,
        candidate_builder: Optional[Callable[[Dict[str, Any], str], bool]] = None,
        opportunities: Optional[Iterable[Dict[str, Any]]] = None,
    ) -> SICReport:
        critique = self.analyze(observation)
        proposals = self._proposals(observation, critique)
        experiment: Dict[str, Any] = {"executed": False, "reason": "No experiment engine configured"}
        decision = "defer"
        if self.improvement is not None and candidate_builder is not None:
            experiment = self.improvement.improve(
                list(opportunities or proposals), candidate_builder
            )
            decision = "adopt" if experiment.get("accepted", 0) else "reject"
        elif opportunities:
            experiment = {
                "executed": False,
                "reason": "Candidate builder required; source changes remain prohibited",
            }
        return SICReport(observation, critique, proposals, experiment, decision)

    def observations(self) -> List[Dict[str, Any]]:
        return [item.to_dict() for item in self._observations]

    def _proposals(
        self, observation: SelfObservation, critique: Mapping[str, Any]
    ) -> List[Dict[str, Any]]:
        reasoning_suggestion = (
            "Resolve the detected uncertainty before execution."
            if critique.get("research_required") or critique.get("ask_user")
            else "Record assumptions and verify them before execution."
        )
        proposals = [
            {
                "id": f"{observation.task_id}:verification",
                "type": "testing",
                "category": "quality",
                "suggestion": "Add a regression test for the observed task outcome.",
            },
            {
                "id": f"{observation.task_id}:uncertainty",
                "type": "refactor",
                "category": "reasoning",
                "suggestion": reasoning_suggestion,
            },
            {
                "id": f"{observation.task_id}:recovery",
                "type": "bug",
                "category": "reliability",
                "suggestion": "Add failure classification and an explicit recovery path.",
            },
        ]
        if observation.failures:
            diagnosis = self.meta.propose_debug_repair(observation.failures[0])
            proposals[2]["diagnosis"] = diagnosis.to_dict()
        return proposals
