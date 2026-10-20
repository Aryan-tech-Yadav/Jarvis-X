import json
import time
from collections import defaultdict


class MetricsManager:
    def __init__(self):
        self.values = defaultdict(float)
        self.runtimes = []

    def record(self, name, value=1):
        self.values[name] += value

    def record_runtime(self, seconds):
        self.runtimes.append(float(seconds))

    def record_ai_call(self, prompt_tokens=0, response_tokens=0):
        self.record("ai_calls")
        self.record("prompt_tokens", prompt_tokens)
        self.record("response_tokens", response_tokens)

    def export(self):
        result = dict(self.values)
        result["average_runtime"] = sum(self.runtimes) / len(self.runtimes) if self.runtimes else 0.0
        result["success_rate"] = 1.0 - result.get("failures", 0) / result.get("tool_calls", 1)
        return result