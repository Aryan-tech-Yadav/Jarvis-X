from .ambiguity_detector import AmbiguityDetector
from .constraint_analyzer import ConstraintAnalyzer
from .feature_extractor import FeatureExtractor
from .priority_detector import PriorityDetector
from .requirement_summary import RequirementSummary
from .requirement_validator import RequirementValidator


class RequirementManager:
    """Public requirement-analysis facade used by the brain pipeline."""

    def __init__(self, extractor=None, ambiguity_detector=None, constraint_analyzer=None,
                 priority_detector=None, validator=None, summarizer=None):
        self.extractor = extractor or FeatureExtractor()
        self.ambiguity_detector = ambiguity_detector or AmbiguityDetector()
        self.constraint_analyzer = constraint_analyzer or ConstraintAnalyzer()
        self.priority_detector = priority_detector or PriorityDetector()
        self.validator = validator or RequirementValidator()
        self.summarizer = summarizer or RequirementSummary()

    def analyze(self, goal):
        if not isinstance(goal, str):
            raise ValueError("Goal must be a string")
        goal = goal.strip()
        features = self.extractor.extract(goal)
        analysis = {
            "goal": goal,
            "features": features,
            "constraints": self.constraint_analyzer.analyze(goal),
            "priorities": self.priority_detector.prioritize(features),
        }
        analysis["ambiguities"] = self.ambiguity_detector.detect(goal, features)
        analysis["clarifying_questions"] = self._questions(analysis)
        analysis.update(self.validator.validate(analysis))
        analysis["summary"] = self.summarizer.build(analysis)
        return analysis

    @staticmethod
    def _questions(analysis):
        questions = []
        if "Target platform is not specified." in analysis["ambiguities"]:
            questions.append("Should this be a web app, mobile app, desktop app, API, or CLI?")
        if "authentication" not in analysis["features"]:
            questions.append("Do users need accounts or should the first version be anonymous?")
        if not analysis["constraints"]:
            questions.append("What deadline, budget, privacy, or scale constraints should guide the design?")
        return questions
