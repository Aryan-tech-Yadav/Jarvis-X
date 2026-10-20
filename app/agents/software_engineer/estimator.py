"""Project estimation facade."""

from app.engineering.complexity_estimator import ComplexityEstimator


class Estimator:
    def __init__(self, estimator=None):
        self.estimator = estimator or ComplexityEstimator()

    def estimate(self, requirements, architecture=None, technology=None):
        data = requirements.to_dict()
        data["features"] = list(requirements.features)
        if technology is not None:
            data["tech_stack"] = technology.to_dict()
        return self.estimator.estimate(data, architecture.to_dict() if architecture else None)

