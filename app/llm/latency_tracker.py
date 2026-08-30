from collections import defaultdict
from typing import Dict, List


class LatencyTracker:
    def __init__(self):
        self.samples: Dict[str, List[float]] = defaultdict(list)

    def record(self, model, seconds):
        self.samples[model].append(float(seconds))

    def average(self, model):
        values = self.samples.get(model, [])
        return sum(values) / len(values) if values else None