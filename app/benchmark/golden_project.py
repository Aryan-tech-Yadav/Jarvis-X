from dataclasses import dataclass, field


@dataclass(frozen=True)
class GoldenProject:
    """A stable, representative engineering benchmark specification."""

    identifier: str
    title: str
    goal: str
    tier: str
    required_features: tuple = field(default_factory=tuple)
    requires_approval: bool = False

    def to_dict(self):
        return {
            "id": self.identifier,
            "title": self.title,
            "goal": self.goal,
            "tier": self.tier,
            "required_features": list(self.required_features),
            "requires_approval": self.requires_approval,
        }
