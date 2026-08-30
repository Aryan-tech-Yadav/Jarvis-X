"""Event history facade."""

from typing import Optional

from app.events.event import Event
from app.eos.event_bus import EventBus


class EventHistory:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus

    def search(self, event_type: Optional[str] = None, limit: int = 100):
        return self.event_bus.get_history(event_type, limit)

    def clear(self) -> None:
        self.event_bus.clear_history()
