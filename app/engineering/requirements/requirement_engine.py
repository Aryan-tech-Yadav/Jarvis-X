"""Requirement intelligence engine for pre-coding analysis."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from app.engineering.requirements.acceptance_criteria import AcceptanceCriteriaGenerator
from app.engineering.requirements.ambiguity_detector import AmbiguityDetector
from app.engineering.requirements.question_generator import QuestionGenerator
from app.engineering.requirements.requirement_classifier import RequirementClassifier
from app.engineering.requirements.requirement_parser import RequirementParser
from app.engineering.requirements.risk_detector import RiskDetector
from app.engineering.requirements.scope_estimator import ScopeEstimator
from app.engineering.technology_selector import TechnologySelector


@dataclass
class RequirementReport:
    """Complete analysis output produced before coding starts."""

    goal: str
    project_type: str
    domain: str
    functional_requirements: list[str] = field(default_factory=list)
    non_functional_requirements: list[str] = field(default_factory=list)
    business_rules: list[str] = field(default_factory=list)
    user_roles: list[str] = field(default_factory=list)
    features: list[str] = field(default_factory=list)
    risks: Dict[str, Any] = field(default_factory=dict)
    questions: list[str] = field(default_factory=list)
    ambiguities: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)
    complexity: Dict[str, Any] = field(default_factory=dict)
    tech_stack: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "goal": self.goal,
            "project_type": self.project_type,
            "domain": self.domain,
            "functional_requirements": list(self.functional_requirements),
            "non_functional_requirements": list(self.non_functional_requirements),
            "business_rules": list(self.business_rules),
            "user_roles": list(self.user_roles),
            "features": list(self.features),
            "risks": dict(self.risks),
            "questions": list(self.questions),
            "ambiguities": list(self.ambiguities),
            "acceptance_criteria": list(self.acceptance_criteria),
            "complexity": dict(self.complexity),
            "tech_stack": dict(self.tech_stack),
        }

    def to_json(self) -> str:
        import json
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def to_markdown(self) -> str:
        questions = [f"- {item}" for item in self.questions] or ["- None"]
        lines = [
            f"# Requirement Report: {self.goal}",
            "",
            f"- **Project type:** {self.project_type}",
            f"- **Domain:** {self.domain}",
            "",
            "## Functional Requirements",
            *[f"- {item}" for item in self.functional_requirements],
            "",
            "## Non-functional Requirements",
            *[f"- {item}" for item in self.non_functional_requirements],
            "",
            "## User Roles",
            *[f"- {item}" for item in self.user_roles],
            "",
            "## Questions",
            *questions,
            "",
            "## Acceptance Criteria",
            *[f"- {item}" for item in self.acceptance_criteria],
        ]
        return "\n".join(lines)


class RequirementEngine:
    """Compose requirement intelligence services into one stable report."""

    def __init__(
        self,
        parser: Optional[RequirementParser] = None,
        classifier: Optional[RequirementClassifier] = None,
        ambiguity_detector: Optional[AmbiguityDetector] = None,
        question_generator: Optional[QuestionGenerator] = None,
        acceptance_criteria: Optional[AcceptanceCriteriaGenerator] = None,
        risk_detector: Optional[RiskDetector] = None,
        scope_estimator: Optional[ScopeEstimator] = None,
        technology_selector: Optional[TechnologySelector] = None,
    ):
        self.parser = parser or RequirementParser()
        self.classifier = classifier or RequirementClassifier()
        self.ambiguity_detector = ambiguity_detector or AmbiguityDetector()
        self.question_generator = question_generator or QuestionGenerator()
        self.acceptance_criteria = acceptance_criteria or AcceptanceCriteriaGenerator()
        self.risk_detector = risk_detector or RiskDetector()
        self.scope_estimator = scope_estimator or ScopeEstimator()
        self.technology_selector = technology_selector or TechnologySelector()

    def analyze(self, goal: str) -> RequirementReport:
        if not isinstance(goal, str) or not goal.strip():
            raise ValueError("Project goal cannot be empty")
        requirements = self.parser.parse(goal.strip())
        ambiguities = self.ambiguity_detector.detect(goal, requirements)
        questions = self.question_generator.generate(goal, requirements)
        classification = self.classifier.classify(requirements)
        tech_stack = self.technology_selector.select(requirements.to_dict()).to_dict()
        requirements.tech_stack = tech_stack
        return RequirementReport(
            goal=goal.strip(),
            project_type=classification["project_type"],
            domain=classification["domain"],
            functional_requirements=list(requirements.features),
            non_functional_requirements=list(requirements.non_functional),
            user_roles=list(requirements.roles),
            business_rules=self._business_rules(requirements),
            features=list(requirements.features),
            risks=self.risk_detector.detect(requirements),
            questions=list(dict.fromkeys([*questions, *ambiguities])),
            ambiguities=ambiguities,
            acceptance_criteria=self.acceptance_criteria.generate(requirements),
            complexity=self.scope_estimator.estimate(requirements),
            tech_stack=tech_stack,
        )

    @staticmethod
    def _business_rules(requirements) -> list[str]:
        rules = ["All submitted data must pass validation before persistence."]
        if "payments" in requirements.features:
            rules.append("Payment operations must be authorized and auditable.")
        if "authentication" in requirements.features:
            rules.append("Protected features require an authenticated user.")
        return rules
