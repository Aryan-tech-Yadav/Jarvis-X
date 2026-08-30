"""EOS telemetry collector."""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Telemetry:
    events: List[Dict[str, Any]] = field(default_factory=list)

    def record(self, event: str, **data: Any) -> None:
        self.events.append({"event": event, **data})

    def snapshot(self) -> List[Dict[str, Any]]:
        return list(self.events)
