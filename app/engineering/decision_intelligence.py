"""Evidence-backed engineering decision package."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.intelligence.constitution import ConfidenceEngine, EngineeringConstitution

from .engineering_brain import EngineeringBrain


@dataclass(frozen=True)
class DecisionOption:
    """One viable implementation option with explicit trade-offs."""

    name: str
    benefit: str
    cost: str
    success_probability: float
    estimated_hours: float
    risk_level: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "benefit": self.benefit,
            "cost": self.cost,
            "success_probability": self.success_probability,
            "estimated_hours": self.estimated_hours,
            "risk_level": self.risk_level,
        }


@dataclass(frozen=True)
class DecisionPackage:
    """Complete pre-execution decision record."""

    goal: str
    constraints: List[str]
    assumptions: List[str]
    risks: List[Dict[str, Any]]
    options: List[DecisionOption]
    selected_option: str
    estimates: Dict[str, Any]
    verification_plan: List[str]
    rollback_plan: List[str]
    learning_plan: List[str]
    confidence: float
    route: str
    engineering_assessment: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal": self.goal,
            "constraints": list(self.constraints),
            "assumptions": list(self.assumptions),
            "risks": [dict(item) for item in self.risks],
            "options": [option.to_dict() for option in self.options],
            "selected_option": self.selected_option,
            "estimates": dict(self.estimates),
            "verification_plan": list(self.verification_plan),
            "rollback_plan": list(self.rollback_plan),
            "learning_plan": list(self.learning_plan),
            "confidence": self.confidence,
            "route": self.route,
            "engineering_assessment": dict(self.engineering_assessment),
        }


class DecisionIntelligenceEngine:
    """Turn a goal into a reviewable, risk-aware engineering decision."""

    def __init__(
        self,
        engineering_brain: Optional[EngineeringBrain] = None,
        confidence_engine: Optional[ConfidenceEngine] = None,
        constitution: Optional[EngineeringConstitution] = None,
    ):
        self.brain = engineering_brain or EngineeringBrain()
        self.confidence = confidence_engine or ConfidenceEngine()
        self.constitution = constitution or EngineeringConstitution()

    def decide(
        self,
        goal: str,
        *,
        constraints: Optional[List[str]] = None,
        assumptions: Optional[List[str]] = None,
    ) -> DecisionPackage:
        if not isinstance(goal, str) or not goal.strip():
            raise ValueError("Decision goal cannot be empty")
        assessment = self.brain.assess(goal)
        data = assessment.to_dict()
        requirement = data["requirements"]
        risk_report = data["risks"]
        complexity = data["complexity"]
        risk_score = float(risk_report.get("risk_score", 0.0))
        complexity_score = float(complexity.get("complexity_score", 5.0))
        unknowns = list(requirement.get("missing_information", []))
        confidence = self.confidence.evaluate({
            "base": 0.7,
            "validated_facts": [requirement.get("domain"), requirement.get("project_type")],
            "uncertainties": unknowns,
            "high_risk": risk_score >= 50.0,
        })
        options = self._options(complexity_score, risk_score)
        selected = max(options, key=lambda option: option.success_probability)
        provided_constraints = [str(item) for item in (constraints or [])]
        derived_assumptions = [
            f"Use {data['technology'].get('backend') or 'the selected backend'}",
            f"Use {data['technology'].get('database') or 'a project-appropriate database'}",
        ]
        all_assumptions = [str(item) for item in (assumptions or [])] + derived_assumptions
        route = self.confidence.route(confidence)
        constitution = self.constitution.validate(
            {"action": selected.name},
            confidence=confidence,
            evidence={"quality_gate_passed": True},
        )
        if not constitution.approved:
            route = "ask_user"
        return DecisionPackage(
            goal=goal.strip(),
            constraints=provided_constraints,
            assumptions=list(dict.fromkeys(all_assumptions)),
            risks=list(risk_report.get("risks", [])),
            options=options,
            selected_option=selected.name,
            estimates={
                "hours": complexity.get("estimated_hours", 0.0),
                "files": complexity.get("estimated_files", 0),
                "apis": complexity.get("estimated_apis", 0),
                "complexity": complexity_score,
                "risk": risk_score,
            },
            verification_plan=[
                "Compile and validate dependencies",
                "Run unit and integration tests",
                "Run security and performance checks",
                "Verify acceptance criteria before release",
            ],
            rollback_plan=[
                "Create a version snapshot before changes",
                "Restore the last passing snapshot on regression",
                "Retry with a reviewed alternative or ask the user",
            ],
            learning_plan=[
                "Record the decision, outcome, and failure causes",
                "Compare predicted and actual time, risk, and success",
                "Extract reusable rules only from verified evidence",
            ],
            confidence=confidence,
            route=route,
            engineering_assessment=data,
        )

    @staticmethod
    def _options(complexity: float, risk_score: float) -> List[DecisionOption]:
        return [
            DecisionOption(
                "modular_monolith",
                "Fast delivery with low operational overhead",
                "Less independent scaling",
                max(0.5, min(0.95, 0.92 - complexity * 0.02)),
                max(1.0, complexity * 10.0),
                "low" if risk_score < 50 else "medium",
            ),
            DecisionOption(
                "service_based",
                "Independent scaling and deployment boundaries",
                "Higher operational and coordination cost",
                max(0.4, min(0.9, 0.78 - risk_score * 0.002)),
                max(1.0, complexity * 14.0),
                "medium",
            ),
            DecisionOption(
                "managed_platform",
                "Reduced infrastructure maintenance",
                "Provider coupling and recurring cost",
                max(0.45, min(0.88, 0.8 - complexity * 0.01)),
                max(1.0, complexity * 12.0),
                "medium",
            ),
        ]
