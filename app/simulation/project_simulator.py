from app.simulation.simulation_engine import SimulationEngine


class ProjectSimulator:
    def __init__(self, engine=None):
        self.engine = engine or SimulationEngine()

    def simulate(self, requirements, architecture=None, strategy=None):
        return self.engine.simulate(requirements, architecture, strategy).to_dict()
