from copy import deepcopy


class StrategyHistory:
    """In-memory experience store used by strategy selection.

    Persistence remains the responsibility of the existing learning subsystem.
    """

    def __init__(self):
        self._records = []

    def record(self, goal, strategy, success, metadata=None):
        if not isinstance(goal, str) or not goal.strip():
            raise ValueError("Goal cannot be empty")
        if not isinstance(strategy, str) or not strategy.strip():
            raise ValueError("Strategy cannot be empty")
        record = {"goal": goal.strip(), "strategy": strategy.strip(), "success": bool(success), "metadata": dict(metadata or {})}
        self._records.append(record)
        return deepcopy(record)

    def experience(self, strategy, goal=""):
        name = str(strategy).casefold()
        words = set(str(goal).casefold().split())
        matches = [item for item in self._records if item["strategy"].casefold() == name]
        if words:
            similar = [item for item in matches if words & set(item["goal"].casefold().split())]
            matches = similar or matches
        if not matches:
            return {"attempts": 0, "success_rate": 0.5}
        return {"attempts": len(matches), "success_rate": sum(item["success"] for item in matches) / len(matches)}

    def records(self):
        return deepcopy(self._records)
