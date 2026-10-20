"""Measurable engineering maturity and change governance."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Mapping


MATURITY_LEVELS = (
    (90.0, "EML-5", "Engineering Intelligence Platform"),
    (75.0, "EML-4", "Self-Evolving AI"),
    (60.0, "EML-3", "Self-Healing AI"),
    (40.0, "EML-2", "Reliable AI"),
    (0.0, "EML-1", "Functional AI"),
)

SKILLS = (
    "planning",
    "architecture",
    "debugging",
    "optimization",
    "testing",
    "research",
)


def classify_failure_category(message: str) -> str:
    """Normalize an observed failure into an analytics-friendly category."""
    text = str(message).casefold()
    signals = (
        ("security", ("secret", "auth", "permission", "security")),
        ("dependency", ("import", "package", "dependency", "module")),
        ("environment", ("path", "interpreter", "environment", "python")),
        ("network", ("network", "connection", "http", "socket")),
        ("performance", ("slow", "timeout", "latency", "memory")),
        ("logic", ("assert", "expected", "logic", "valueerror")),
        ("architecture", ("architecture", "design", "coupling")),
        ("planning", ("plan", "requirement", "scope")),
    )
    for category, words in signals:
        if any(word in text for word in words):
            return category
    return "unknown"


@dataclass(frozen=True)
class MaturityScore:
    """Dimension scores and resulting engineering maturity level."""

    dimensions: Dict[str, float]
    overall_score: float
    level: str
    label: str
    weakest_skill: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimensions": dict(self.dimensions),
            "overall_score": self.overall_score,
            "level": self.level,
            "label": self.label,
            "weakest_skill": self.weakest_skill,
        }


@dataclass(frozen=True)
class GovernanceDecision:
    """Auditable approval decision for a proposed engineering change."""

    approved: bool
    risk_score: float
    benchmark_required: bool
    blockers: tuple[str, ...] = ()
    checks: Dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "approved": self.approved,
            "risk_score": self.risk_score,
            "benchmark_required": self.benchmark_required,
            "blockers": list(self.blockers),
            "checks": dict(self.checks),
        }


class EngineeringMaturityEngine:
    """Aggregate evidence into maturity, KPIs, history, and governance."""

    def __init__(self) -> None:
        self._skill_history: list[Dict[str, float]] = []
        self._timeline: list[Dict[str, Any]] = []

    def score(self, evidence: Mapping[str, Any]) -> MaturityScore:
        if not isinstance(evidence, Mapping):
            raise TypeError("Maturity evidence must be a mapping")
        dimensions = {
            name: self._bounded(evidence.get(name, 0.0))
            for name in (
                "requirement_understanding",
                "planning",
                "architecture",
                "code_quality",
                "security",
                "performance",
                "maintainability",
                "testing",
            )
        }
        overall = round(sum(dimensions.values()) / len(dimensions), 2)
        level, label = next((level, label) for threshold, level, label in MATURITY_LEVELS if overall >= threshold)
        skills = {
            skill: self._bounded(evidence.get(skill, dimensions.get(skill, 0.0)))
            for skill in SKILLS
        }
        weakest = min(skills, key=skills.get)
        self._skill_history.append(skills)
        self._timeline.append({
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "overall_score": overall,
            "level": level,
        })
        return MaturityScore(dimensions, overall, level, label, weakest)

    def skill_graph(self) -> Dict[str, Any]:
        current = self._skill_history[-1] if self._skill_history else {skill: 0.0 for skill in SKILLS}
        return {
            "skills": dict(current),
            "weakest_skill": min(current, key=current.get),
            "history": [dict(item) for item in self._skill_history],
        }

    def timeline(self) -> list[Dict[str, Any]]:
        return [dict(item) for item in self._timeline]

    def kpis(self, records: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
        values = list(records)
        quality = [float(item.get("quality", {}).get("overall_score", 0.0)) for item in values]
        successful = sum(bool(item.get("reliability", {}).get("success")) for item in values)
        return {
            "projects": len(values),
            "success_rate": round(successful / len(values), 4) if values else 0.0,
            "average_quality": round(sum(quality) / len(quality), 2) if quality else 0.0,
            "failure_categories": self.failure_taxonomy(values),
        }

    @staticmethod
    def failure_taxonomy(records: Iterable[Mapping[str, Any]]) -> Dict[str, int]:
        categories: Dict[str, int] = {}
        for record in records:
            for failure in record.get("failures", []):
                category = str(failure.get("error_category") or classify_failure_category(
                    failure.get("failure", failure.get("root_cause", "unknown"))
                ))
                categories[category] = categories.get(category, 0) + 1
        return categories

    @staticmethod
    def govern(change: Mapping[str, Any]) -> GovernanceDecision:
        if not isinstance(change, Mapping):
            raise TypeError("Change proposal must be a mapping")
        checks = {
            "impact_analyzed": bool(change.get("impact_analyzed")),
            "backward_compatible": bool(change.get("backward_compatible")),
            "security_reviewed": bool(change.get("security_reviewed")),
            "performance_acceptable": bool(change.get("performance_acceptable")),
            "rollback_possible": bool(change.get("rollback_possible")),
        }
        risk = max(0.0, min(100.0, float(change.get("risk_score", 100.0))))
        benchmark_required = bool(change.get("benchmark_required", risk >= 30.0))
        benchmark_passed = bool(change.get("benchmark_passed")) if benchmark_required else True
        blockers = [name for name, passed in checks.items() if not passed]
        if benchmark_required and not benchmark_passed:
            blockers.append("benchmark_passed")
        return GovernanceDecision(
            approved=not blockers,
            risk_score=round(risk, 2),
            benchmark_required=benchmark_required,
            blockers=tuple(blockers),
            checks=checks,
        )

    @staticmethod
    def _bounded(value: Any) -> float:
        return round(max(0.0, min(100.0, float(value))), 2)
