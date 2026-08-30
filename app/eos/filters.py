"""Composable event filters."""

from typing import Callable

from app.events.event import Event


def event_type_filter(event_type: str) -> Callable[[Event], bool]:
    return lambda event: event.event_type == event_type
