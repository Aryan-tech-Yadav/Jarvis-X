from datetime import datetime, timezone


class AuditLogger:
    def __init__(self):
        self._events = []

    def record(self, decision, *, input_data=None, output_data=None, confidence=None, risk=None):
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "decision": decision,
            "input": input_data or {},
            "output": output_data or {},
            "confidence": confidence,
            "risk": risk,
        }
        self._events.append(event)
        return event

    def events(self):
        return list(self._events)
