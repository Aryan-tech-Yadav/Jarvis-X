"""Feature identification facade."""

from app.requirements.feature_extractor import FeatureExtractor


class FeatureIdentifier:
    def __init__(self, extractor=None):
        self.extractor = extractor or FeatureExtractor()

    def identify(self, goal: str) -> list[str]:
        return self.extractor.extract(goal)

