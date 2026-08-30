from dataclasses import dataclass, field


@dataclass
class RequirementModel:
    functional: list[str] = field(default_factory=list)
    non_functional: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    questions: list[str] = field(default_factory=list)

    def to_dict(self):
        return {"functional": list(self.functional), "non_functional": list(self.non_functional),
                "constraints": list(self.constraints), "missing": list(self.missing), "questions": list(self.questions)}
