from dataclasses import dataclass, field


@dataclass
class ArchitectureModel:
    pattern: str
    tech_stack: dict = field(default_factory=dict)
    entities: list[str] = field(default_factory=list)
    relationships: list[dict] = field(default_factory=list)
    endpoints: list[dict] = field(default_factory=list)
    rationale: str = ""

    def to_dict(self):
        return {"pattern": self.pattern, "tech_stack": dict(self.tech_stack), "entities": list(self.entities),
                "relationships": list(self.relationships), "endpoints": list(self.endpoints), "rationale": self.rationale}
