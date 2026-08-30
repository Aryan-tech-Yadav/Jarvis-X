from dataclasses import dataclass


@dataclass(frozen=True)
class BenchmarkCase:
    name: str
    expected: object = True
    weight: float = 1.0
    category: str = "general"

    def evaluate(self, actual):
        if callable(self.expected):
            passed = bool(self.expected(actual))
        else:
            passed = actual == self.expected
        return {"name": self.name, "category": self.category, "passed": passed, "weight": max(0.0, float(self.weight)), "actual": actual}
