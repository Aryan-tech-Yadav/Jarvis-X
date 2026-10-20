"""Requirement classification helpers."""


class RequirementClassifier:
    def classify(self, requirements) -> dict:
        return {
            "project_type": requirements.project_type,
            "domain": requirements.domain,
            "roles": list(requirements.roles),
            "features": list(requirements.features),
        }

