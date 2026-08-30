from dataclasses import dataclass, field


@dataclass(frozen=True)
class SimulationResult:
    estimated_files: int
    estimated_minutes: int
    dependencies: tuple
    risks: tuple
    missing_requirements: tuple = field(default_factory=tuple)
    confidence: float = 0.5

    def to_dict(self):
        return {"estimated_files": self.estimated_files, "estimated_minutes": self.estimated_minutes, "dependencies": list(self.dependencies), "risks": list(self.risks), "missing_requirements": list(self.missing_requirements), "confidence": self.confidence}
