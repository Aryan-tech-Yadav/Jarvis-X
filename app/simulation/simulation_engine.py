from app.simulation.dependency_simulator import DependencySimulator
from app.simulation.risk_simulator import RiskSimulator
from app.simulation.simulation_result import SimulationResult


class SimulationEngine:
    def __init__(self, dependencies=None, risks=None):
        self.dependencies = dependencies or DependencySimulator()
        self.risks = risks or RiskSimulator()

    def simulate(self, requirements, architecture=None, strategy=None):
        features = requirements.get("features", ())
        modules = (architecture or {}).get("modules", ())
        strategy_minutes = int((strategy or {}).get("estimated_minutes", 30))
        estimated_files = max(3, 3 + len(features) * 3 + len(modules))
        risk_items = self.risks.estimate(requirements, architecture)
        missing = tuple(requirements.get("clarifying_questions", ()))
        confidence = round(max(0.2, 0.9 - 0.06 * len(risk_items) - 0.04 * len(missing)), 2)
        return SimulationResult(
            estimated_files=estimated_files,
            estimated_minutes=strategy_minutes + len(features) * 8,
            dependencies=tuple(self.dependencies.estimate(requirements, architecture)),
            risks=tuple(risk_items),
            missing_requirements=missing,
            confidence=confidence,
        )
