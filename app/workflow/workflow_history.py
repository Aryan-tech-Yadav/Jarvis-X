from datetime import datetime, timezone


class WorkflowHistory:
    def __init__(self):
        self._events = []

    def record(self, event, step_id=None, details=None):
        entry = {
            "event": event,
            "step_id": step_id,
            "details": dict(details or {}),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._events.append(entry)
        return entry

    def events(self):
        return list(self._events)
