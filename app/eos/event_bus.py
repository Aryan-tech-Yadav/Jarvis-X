"""EOS event bus facade with typed-event and replay compatibility."""

from app.events.event_bus import EventBus as LegacyEventBus
from app.events.event import Event


class EOSEventBus(LegacyEventBus):
    def publish(self, event_type, payload=None):
        if isinstance(event_type, Event):
            event = event_type
            published = super().publish(event.event_type, event.payload)
            if published is not None:
                published.event_id = event.event_id
                published.source = event.source
                published.target = event.target
                published.priority = event.priority
                published.metadata = dict(event.metadata)
            return published
        return super().publish(event_type, payload)

    def emit(self, event):
        return self.publish(event)

    def clear(self):
        self.clear_history()


EventBus = EOSEventBus

__all__ = ["EventBus", "EOSEventBus", "Event"]
