"""Memory-aware context provider for reasoning."""

from typing import Any, Dict


class MemoryReasoner:
    def __init__(self, memory=None):
        self.memory = memory

    def recall(self, goal: str) -> Dict[str, Any]:
        if self.memory is None:
            return {}
        search = getattr(self.memory, "search", None)
        if not callable(search):
            return {}
        return {"related": search(goal)}

    def learn(self, goal: str, reflection: Dict[str, Any]) -> Any:
        if self.memory is None:
            return None
        store = getattr(self.memory, "store", None) or getattr(self.memory, "save", None)
        if callable(store):
            return store(goal, reflection)
        return None

