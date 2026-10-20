"""Scope estimation facade."""

from app.engineering.complexity_estimator import ComplexityEstimator


class ScopeEstimator:
    def __init__(self, estimator=None):
        self.estimator = estimator or ComplexityEstimator()

    def estimate(self, requirements) -> dict:
        return self.estimator.estimate(requirements.to_dict()).to_dict()

