import os

from config import WORKSPACE


class HealthChecker:
    def __init__(self, ai=None, memory=None, tools=None, event_bus=None, runtime=None):
        self.ai = ai
        self.memory = memory
        self.tools = tools
        self.event_bus = event_bus
        self.runtime = runtime

    def check(self):
        checks = {
            "ai": self._ai_ok(),
            "workspace": os.path.isdir(WORKSPACE),
            "memory": self._memory_ok(),
            "tools": self.tools is None or bool(self.tools.names()),
            "event_bus": self.event_bus is None or self.event_bus.alive(),
            "config": bool(WORKSPACE),
            "runtime": self.runtime is None or bool(self.runtime.health().get("healthy")),
        }
        return {"healthy": all(checks.values()), "checks": checks}

    def _ai_ok(self):
        return self.ai is not None

    def _memory_ok(self):
        if self.memory is None:
            return os.path.isdir("data")
        try:
            return isinstance(self.memory.load_memory(), dict)
        except Exception:
            return False
