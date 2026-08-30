"""Engineering task decomposition facade."""

from app.engineering.task_breakdown import TaskBreakdownEngine


class TaskBreaker:
    def __init__(self, breaker=None):
        self.breaker = breaker or TaskBreakdownEngine()

    def break_down(self, architecture, requirements):
        return self.breaker.breakdown(architecture, requirements.analysis)

