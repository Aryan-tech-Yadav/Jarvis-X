"""Subscriber protocol for EOS event consumers."""

from typing import Protocol

from app.events.event import Event


class EventSubscriber(Protocol):
    def __call__(self, event: Event) -> None: ...
