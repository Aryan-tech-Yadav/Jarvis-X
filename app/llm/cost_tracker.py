from collections import defaultdict
from typing import Dict


class CostTracker:
    def __init__(self):
        self.total = 0.0
        self.by_model: Dict[str, float] = defaultdict(float)

    def record(self, model, cost=0.0):
        value = float(cost or 0.0)
        self.total += value
        self.by_model[model] += value
        return value