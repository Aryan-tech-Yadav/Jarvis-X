from copy import deepcopy
from datetime import datetime, timezone


class ExecutionHistory:
    """Append-only, serializable run history used by reports and replay review."""

    def __init__(self):
        self._entries = []

    def record(self, event_type, *, run_id=None, node_id=None, payload=None):
        entry = {
            "type": str(event_type), "run_id": run_id, "node_id": node_id,
            "payload": deepcopy(payload), "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._entries.append(entry)
        return deepcopy(entry)

    def entries(self, run_id=None):
        values = self._entries if run_id is None else [item for item in self._entries if item["run_id"] == run_id]
        return deepcopy(values)

    def to_dict(self):
        return {"entries": self.entries()}
