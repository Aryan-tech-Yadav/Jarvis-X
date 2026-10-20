"""Deterministic acceptance criteria generation."""


class AcceptanceCriteriaGenerator:
    def generate(self, requirements) -> list[str]:
        criteria = [
            "The project scope and supported platform are explicitly documented.",
            "Every listed functional requirement has a testable outcome.",
        ]
        criteria.extend(
            f"The system supports {feature} with automated validation."
            for feature in requirements.features
        )
        criteria.extend(
            f"The system satisfies the {requirement} non-functional requirement."
            for requirement in requirements.non_functional
        )
        return list(dict.fromkeys(criteria))

