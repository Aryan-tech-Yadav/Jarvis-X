"""Event-bus adapter for message delivery notifications."""

from __future__ import annotations

from typing import Callable, Optional

from app.events.event_bus import EventBus

from .event import CommunicationEvent
from .message import AgentMessage


class CommunicationEventBus:
    """Publish communication events through the existing runtime event bus."""

    MESSAGE_SENT = "AGENT_MESSAGE_SENT"
    MESSAGE_BROADCAST = "AGENT_MESSAGE_BROADCAST"

    def __init__(self, event_bus: Optional[EventBus] = None):
        self._event_bus = event_bus or EventBus()

    def publish_message(self, message: AgentMessage) -> Optional[CommunicationEvent]:
        return self._event_bus.publish(self.MESSAGE_SENT, message.to_dict())

    def publish_broadcast(self, messages) -> Optional[CommunicationEvent]:
        return self._event_bus.publish(
            self.MESSAGE_BROADCAST,
            {"messages": [message.to_dict() for message in messages]},
        )

    def subscribe(self, event_type: str, listener: Callable) -> str:
        return self._event_bus.subscribe(event_type, listener)

