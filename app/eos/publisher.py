"""Publisher protocol for EOS event producers."""

from typing import Any, Protocol

from app.events.event import Event


class EventPublisher(Protocol):
    def publish(self, event_type: Any, payload: Any = None) -> Event: ...
