"""Requirement analysis facade for the software engineer agent."""

from typing import Any, Dict

from app.analysis.requirements.extractor import RequirementExtractor
from app.engineering.requirement_analyzer import RequirementAnalyzer as EngineeringRequirementAnalyzer


class ProjectRequirements:
    """Combined requirement analysis and functional requirement model."""

    def __init__(self, analysis: Any, model: Any):
        self.analysis = analysis
        self.model = model
        self.functional = model.functional
        self.non_functional = model.non_functional
        self.questions = model.questions
        self.missing = model.missing
        self.features = model.functional
        self.tech_stack: Dict[str, Any] = {}

    def __getattr__(self, name: str) -> Any:
        return getattr(self.analysis, name)

    def to_dict(self) -> dict:
        data = self.analysis.to_dict()
        data.update(self.model.to_dict())
        data["features"] = list(self.features)
        data["tech_stack"] = dict(self.tech_stack)
        return data


class RequirementAnalyzer:
    """Compose the existing engineering and requirements analyzers."""

    def __init__(self, analyzer=None, extractor=None):
        self.analyzer = analyzer or EngineeringRequirementAnalyzer()
        self.extractor = extractor or RequirementExtractor()

    def analyze(self, goal: str) -> ProjectRequirements:
        analysis = self.analyzer.analyze(goal)
        if analysis.domain == "general" and "e-commerce" in goal.casefold():
            analysis.domain = "ecommerce"
        model = self.extractor.extract(goal, {"features": analysis.modules})
        requirements = ProjectRequirements(analysis, model)
        requirements.missing = list(analysis.missing_information) + list(model.missing)
        requirements.questions = list(model.questions)
        return requirements
