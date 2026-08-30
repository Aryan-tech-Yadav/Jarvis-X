from typing import Dict, Iterable, Optional


class ModelSelector:
    def __init__(self, models: Optional[Dict[str, Dict[str, object]]] = None):
        self.models = models or {}

    def select(self, task_type="general", candidates: Optional[Iterable[str]] = None) -> Optional[str]:
        names = list(candidates or self.models)
        if not names:
            return None
        eligible = [name for name in names if name in self.models]
        if not eligible:
            return names[0]
        return max(
            eligible,
            key=lambda name: (
                self.models[name].get("coding", 0) if task_type == "coding" else 0,
                -self.models[name].get("cost", 0),
                -self.models[name].get("latency", 0),
            ),
        )