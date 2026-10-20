"""Non-functional requirement analysis."""

from app.analysis.requirements.extractor import RequirementExtractor


class NonFunctionalAnalyzer:
    def __init__(self, extractor=None):
        self.extractor = extractor or RequirementExtractor()

    def analyze(self, goal: str) -> list[str]:
        return self.extractor.extract(goal).non_functional

