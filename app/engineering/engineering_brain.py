"""Unified engineering decision layer over existing deterministic analyzers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from app.intelligence.strategy import StrategyManager

from .architecture_designer import ArchitectureDesigner
from .complexity_estimator import ComplexityEstimator
from .pattern_selector import PatternSelector
from .requirement_analyzer import RequirementAnalysis, RequirementAnalyzer
from .risk_analyzer import RiskAnalyzer
from .technology_selector import TechnologySelector


@dataclass
class EngineeringDecisionReport:
    """Serializable engineering decisions made before implementation."""

    goal: str
    requirements: RequirementAnalysis
    architecture: Any
    technology: Any
    patterns: list[Any] = field(default_factory=list)
    risks: Any = None
    complexity: Any = None
    strategy: Dict[str, Any] = field(default_factory=dict)
    tradeoffs: list[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal": self.goal,
            "requirements": self.requirements.to_dict(),
            "architecture": self.architecture.to_dict(),
            "technology": self.technology.to_dict(),
            "patterns": [pattern.to_dict() for pattern in self.patterns],
            "risks": self.risks.to_dict() if self.risks is not None else {},
            "complexity": self.complexity.to_dict() if self.complexity is not None else {},
            "strategy": dict(self.strategy),
            "tradeoffs": [dict(item) for item in self.tradeoffs],
        }


class EngineeringBrain:
    """Coordinate engineering analysis without executing project changes."""

    def __init__(
        self,
        requirement_analyzer: Optional[RequirementAnalyzer] = None,
        architecture_designer: Optional[ArchitectureDesigner] = None,
        technology_selector: Optional[TechnologySelector] = None,
        pattern_selector: Optional[PatternSelector] = None,
        risk_analyzer: Optional[RiskAnalyzer] = None,
        complexity_estimator: Optional[ComplexityEstimator] = None,
        strategy_manager: Optional[StrategyManager] = None,
    ):
        self.requirement_analyzer = requirement_analyzer or RequirementAnalyzer()
        self.architecture_designer = architecture_designer or ArchitectureDesigner()
        self.technology_selector = technology_selector or TechnologySelector()
        self.pattern_selector = pattern_selector or PatternSelector()
        self.risk_analyzer = risk_analyzer or RiskAnalyzer()
        self.complexity_estimator = complexity_estimator or ComplexityEstimator()
        self.strategy_manager = strategy_manager or StrategyManager()

    def assess(self, goal: str) -> EngineeringDecisionReport:
        """Produce pre-implementation engineering decisions for a goal."""
        if not isinstance(goal, str) or not goal.strip():
            raise ValueError("Engineering goal cannot be empty")

        requirements = self.requirement_analyzer.analyze(goal)
        requirement_data = requirements.to_dict()
        architecture = self.architecture_designer.design(goal, requirements)
        technology = self.technology_selector.select(requirement_data)
        patterns = self.pattern_selector.select(requirement_data)
        risk_report = self.risk_analyzer.analyze(requirement_data, architecture.to_dict())
        complexity = self.complexity_estimator.estimate(
            requirement_data, architecture.to_dict()
        )
        strategy = self.strategy_manager.choose(
            goal,
            {
                "domain": requirements.domain,
                "project_type": requirements.project_type,
                "features": list(requirements.keywords),
            },
        ).to_dict()
        return EngineeringDecisionReport(
            goal=goal.strip(),
            requirements=requirements,
            architecture=architecture,
            technology=technology,
            patterns=patterns,
            risks=risk_report,
            complexity=complexity,
            strategy=strategy,
            tradeoffs=self._tradeoffs(requirements, technology),
        )

    @staticmethod
    def _tradeoffs(
        requirements: RequirementAnalysis,
        technology: Any,
    ) -> list[Dict[str, str]]:
        tradeoffs = [{
            "decision": "modular monolith",
            "benefit": "Lower operational complexity and faster iteration",
            "cost": "Less independent scaling than microservices",
        }]
        if technology.cache:
            tradeoffs.append({
                "decision": technology.cache,
                "benefit": "Lower read latency for repeated access",
                "cost": "Additional state invalidation and operational overhead",
            })
        if requirements.project_type == "mobile":
            tradeoffs.append({
                "decision": "shared backend API",
                "benefit": "Consistent business rules across clients",
                "cost": "Requires API versioning for mobile release cadence",
            })
        return tradeoffs
