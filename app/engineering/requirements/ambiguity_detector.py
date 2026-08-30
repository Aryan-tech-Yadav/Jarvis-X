"""Ambiguity detection facade."""

from app.requirements.ambiguity_detector import AmbiguityDetector as ExistingAmbiguityDetector


class AmbiguityDetector:
    def __init__(self, detector=None):
        self.detector = detector or ExistingAmbiguityDetector()

    def detect(self, goal: str, requirements):
        return self.detector.detect(goal, requirements.features)

