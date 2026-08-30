from .architecture.architecture_generator import ArchitectureGenerator
from .complexity_estimator import ComplexityEstimator
from .intent.intent_analyzer import IntentAnalyzer
from .requirements.clarifier import RequirementClarifier
from .requirements.extractor import RequirementExtractor


class AnalysisEngine:
    """Builds the immutable planning input consumed by planning and execution."""

    def __init__(self, intent=None, extractor=None, clarifier=None, architecture=None, complexity=None):
        self.intent = intent or IntentAnalyzer()
        self.extractor = extractor or RequirementExtractor()
        self.clarifier = clarifier or RequirementClarifier()
        self.architecture = architecture or ArchitectureGenerator()
        self.complexity = complexity or ComplexityEstimator()

    def analyze(self, goal, *, requirements=None, architecture=None, risk=None, cost=None):
        base_requirements = requirements or {}
        requirement_model = self.extractor.extract(goal, base_requirements)
        requirement_model = self.clarifier.clarify(goal, requirement_model, base_requirements)
        intent = self.intent.analyze(goal, requirement_model.functional)
        design = self.architecture.generate(goal, requirement_model, intent, base_requirements, architecture)
        complexity = self.complexity.estimate(intent, requirement_model, design, risk or {})
        planning_package = {
            "intent": intent,
            "requirements": requirement_model.to_dict(),
            "architecture": design,
            "database": {"entities": design["entities"], "relationships": design["relationships"]},
            "api": {"endpoints": design["endpoints"]},
            "tech_stack": design["tech_stack"],
            "constraints": list(requirement_model.constraints),
            "risk": dict(risk or {}),
            "complexity": complexity,
            "cost": dict(cost or {}),
            "clarifying_questions": list(requirement_model.questions),
        }
        return {"planning_package": planning_package, "intent": intent, "requirements": requirement_model.to_dict(),
                "architecture": design, "complexity": complexity}
