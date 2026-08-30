from app.cost.optimization import Optimization
from app.cost.resource_cost import ResourceCost
from app.cost.time_cost import TimeCost
from app.cost.token_cost import TokenCost


class CostAnalyzer:
    def __init__(self, token_cost=None, time_cost=None, resource_cost=None, optimization=None):
        self.token_cost = token_cost or TokenCost()
        self.time_cost = time_cost or TimeCost()
        self.resource_cost = resource_cost or ResourceCost()
        self.optimization = optimization or Optimization()

    def analyze(self, simulation, ai_calls=3, tokens_per_call=1200, token_rate=0.0, hourly_rate=0.0):
        tokens = self.token_cost.estimate(ai_calls, tokens_per_call, token_rate)
        time = self.time_cost.estimate(simulation.get("estimated_minutes", 0), hourly_rate)
        resources = self.resource_cost.estimate(simulation.get("estimated_files", 0), len(simulation.get("dependencies", ())))
        return {"tokens": tokens, "time": time, "resources": resources, "estimated_total_cost": round(tokens["estimated_cost"] + time["estimated_cost"], 6), "optimizations": self.optimization.suggest(simulation, tokens)}
