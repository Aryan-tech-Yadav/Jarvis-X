"""Evidence-based lifecycle quality gate for engineering releases."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Mapping


REQUIRED_STAGES = (
    "design",
    "implementation",
    "unit_tests",
    "integration_tests",
    "performance_tests",
    "security_scan",
    "benchmark",
    "reflection",
    "knowledge_update",
)


@dataclass(frozen=True)
class StageResult:
    """Normalized result for one mandatory lifecycle stage."""

    name: str
    passed: bool
    reason: str = ""
    evidence: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "reason": self.reason,
            "evidence": dict(self.evidence),
        }


@dataclass(frozen=True)
class LifecycleGateResult:
    """Auditable quality-gate decision."""

    passed: bool
    score: float
    stages: tuple[StageResult, ...]
    blockers: tuple[str, ...]
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": "lifecycle_quality_gate",
            "passed": self.passed,
            "score": self.score,
            "stages": [stage.to_dict() for stage in self.stages],
            "blockers": list(self.blockers),
            "created_at": self.created_at,
        }


class LifecycleQualityGate:
    """Require explicit evidence for every stage before approving a release."""

    def __init__(self, required_stages=REQUIRED_STAGES, minimum_score: float = 1.0):
        stages = tuple(str(stage) for stage in required_stages)
        if not stages or len(set(stages)) != len(stages):
            raise ValueError("required_stages must contain unique stage names")
        if not 0.0 <= float(minimum_score) <= 1.0:
            raise ValueError("minimum_score must be between 0 and 1")
        self.required_stages = stages
        self.minimum_score = float(minimum_score)

    def evaluate(self, evidence: Mapping[str, Any]) -> LifecycleGateResult:
        """Evaluate stage evidence; missing or failed stages block approval."""
        if not isinstance(evidence, Mapping):
            raise TypeError("Quality-gate evidence must be a mapping")

        stages = tuple(self._stage_result(name, evidence.get(name)) for name in self.required_stages)
        passed_count = sum(stage.passed for stage in stages)
        score = round(passed_count / len(stages), 4)
        blockers = tuple(
            stage.reason or f"{stage.name} did not pass"
            for stage in stages
            if not stage.passed
        )
        return LifecycleGateResult(
            passed=score >= self.minimum_score and not blockers,
            score=score,
            stages=stages,
            blockers=blockers,
        )

    @staticmethod
    def _stage_result(name: str, value: Any) -> StageResult:
        if isinstance(value, bool):
            return StageResult(name=name, passed=value, reason="" if value else f"{name} failed")
        if isinstance(value, Mapping):
            passed = bool(value.get("passed", value.get("success", False)))
            reason = str(value.get("reason", value.get("message", "")))
            if not passed and not reason:
                reason = f"{name} failed"
            return StageResult(name=name, passed=passed, reason=reason, evidence=dict(value))
        return StageResult(name=name, passed=False, reason=f"{name} evidence is missing")
