"""ASEE facade for understanding a software project before coding."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from app.engineering.requirement_engine.clarification_engine import ClarificationEngine
from app.engineering.requirement_engine.constraint_detector import ConstraintDetector
from app.engineering.requirement_engine.domain_detector import DomainDetector
from app.engineering.requirement_engine.feature_identifier import FeatureIdentifier
from app.engineering.requirement_engine.goal_parser import GoalParser
from app.engineering.requirement_engine.requirement_extractor import RequirementExtractor
from app.engineering.requirements.requirement_engine import RequirementEngine as IntelligenceEngine


@dataclass
class RequirementSpec:
    goal: str
    domain: str
    project_type: str
    roles: list[str] = field(default_factory=list)
    modules: list[str] = field(default_factory=list)
    features: list[str] = field(default_factory=list)
    questions: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    risks: Dict[str, Any] = field(default_factory=dict)
    complexity: Dict[str, Any] = field(default_factory=dict)
    tech_stack: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "goal": self.goal,
            "domain": self.domain,
            "project_type": self.project_type,
            "roles": list(self.roles),
            "modules": list(self.modules),
            "features": list(self.features),
            "questions": list(self.questions),
            "constraints": list(self.constraints),
            "risks": dict(self.risks),
            "complexity": dict(self.complexity),
            "tech_stack": dict(self.tech_stack),
        }


class RequirementEngine:
    """Compose existing requirement intelligence into a stable ASEE spec."""

    def __init__(
        self,
        parser: Optional[GoalParser] = None,
        extractor: Optional[RequirementExtractor] = None,
        clarifier: Optional[ClarificationEngine] = None,
        constraints: Optional[ConstraintDetector] = None,
        features: Optional[FeatureIdentifier] = None,
        domains: Optional[DomainDetector] = None,
        intelligence: Optional[IntelligenceEngine] = None,
    ):
        self.parser = parser or GoalParser()
        self.extractor = extractor or RequirementExtractor()
        self.clarifier = clarifier or ClarificationEngine()
        self.constraints = constraints or ConstraintDetector()
        self.features = features or FeatureIdentifier()
        self.domains = domains or DomainDetector()
        self.intelligence = intelligence or IntelligenceEngine()

    def analyze(self, goal: str) -> RequirementSpec:
        normalized = self.parser.parse(goal)
        requirements = self.extractor.extract(normalized)
        questions = self.clarifier.questions(normalized, requirements)
        report = self.intelligence.analyze(normalized)
        features = self.features.identify(normalized)
        modules = list(getattr(requirements, "modules", ()))
        return RequirementSpec(
            goal=normalized,
            domain=self.domains.detect(normalized, requirements),
            project_type=self.domains.project_type(normalized, requirements),
            roles=list(getattr(requirements, "roles", ())),
            modules=modules,
            features=features,
            questions=list(dict.fromkeys(questions + report.questions)),
            constraints=self.constraints.detect(normalized),
            risks=dict(report.risks),
            complexity=dict(report.complexity),
            tech_stack=dict(report.tech_stack),
        )

