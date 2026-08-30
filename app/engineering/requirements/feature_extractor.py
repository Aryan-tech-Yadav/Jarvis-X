"""Feature extraction facade."""

from app.requirements.feature_extractor import FeatureExtractor as ExistingFeatureExtractor


class FeatureExtractor:
    def __init__(self, extractor=None):
        self.extractor = extractor or ExistingFeatureExtractor()

    def extract(self, goal: str) -> list[str]:
        return self.extractor.extract(goal)

