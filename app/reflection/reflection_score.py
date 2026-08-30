from dataclasses import dataclass, field


DEFAULT_AREAS = ("architecture", "performance", "security", "scalability", "maintainability", "testing", "documentation", "readability")


@dataclass
class ReflectionScore:
    scores: dict = field(default_factory=lambda: {area: 0.0 for area in DEFAULT_AREAS})

    @classmethod
    def from_mapping(cls, values):
        scores = {area: min(10.0, max(0.0, float(values.get(area, 0)))) for area in DEFAULT_AREAS}
        return cls(scores)

    @property
    def overall(self):
        return sum(self.scores.values()) / len(self.scores)

    @property
    def weakest_area(self):
        return min(self.scores, key=self.scores.get)
