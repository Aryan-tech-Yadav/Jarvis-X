import json
import os
from copy import deepcopy
from datetime import datetime, timezone


class BenchmarkHistory:
    """Optional JSON persistence for comparable benchmark releases."""

    def __init__(self, path=None):
        self.path = path
        self._runs = self._load() if path else []

    def record(self, report):
        entry = {"recorded_at": datetime.now(timezone.utc).isoformat(), "report": deepcopy(report)}
        self._runs.append(entry)
        if self.path:
            self._save()
        return deepcopy(entry)

    def runs(self):
        return deepcopy(self._runs)

    def latest(self):
        return deepcopy(self._runs[-1]) if self._runs else None

    def _load(self):
        if not os.path.isfile(self.path):
            return []
        try:
            with open(self.path, "r", encoding="utf-8") as source:
                payload = json.load(source)
            return payload if isinstance(payload, list) else []
        except (OSError, json.JSONDecodeError):
            return []

    def _save(self):
        directory = os.path.dirname(os.path.abspath(self.path))
        os.makedirs(directory, exist_ok=True)
        temporary = self.path + ".tmp"
        with open(temporary, "w", encoding="utf-8") as destination:
            json.dump(self._runs, destination, indent=2, sort_keys=True)
        os.replace(temporary, self.path)
