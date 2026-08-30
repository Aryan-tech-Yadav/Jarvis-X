"""Global Event Bus for Jarvis-X runtime.

Provides:
  - Publish/subscribe with async support
  - Event filtering and middleware
  - History with replay capability
  - Wildcard subscriptions
"""

from __future__ import annotations

import asyncio
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Set

from app.events.event import Event
from app.core.logger import Logger


@dataclass
class EventBusStats:
    """Event bus statistics."""
    total_published: int = 0
    total_delivered: int = 0
    total_failed: int = 0
    active_subscriptions: int = 0
    history_size: int = 0


class EventBus:
    """Global event bus for inter-module communication.

    Features:
      - Synchronous and asynchronous event delivery
      - Wildcard subscriptions
      - Event middleware/hooks
      - History with replay
      - Thread-safe operations
      - Event filtering
    """

    def __init__(self, max_history: int = 1000):
        self._listeners: Dict[str, List[Callable]] = {}
        self._wildcard_listeners: List[Callable] = []
        self._middleware: List[Callable] = []
        self._history: List[Event] = []
        self._max_history = max_history
        self._lock = threading.RLock()
        self._stats = EventBusStats()
        self._disabled_types: Set[str] = set()

    def subscribe(self, event_type: str, listener: Callable[[Event], None]) -> str:
        """Subscribe to specific event type.

        Args:
            event_type: Event type to listen for
            listener: Callback function

        Returns:
            Subscription ID for unsubscription
        """
        with self._lock:
            if event_type not in self._listeners:
                self._listeners[event_type] = []
            self._listeners[event_type].append(listener)
            self._stats.active_subscriptions = sum(len(v) for v in self._listeners.values())
            return f"sub_{event_type}_{id(listener)}"

    @property
    def history(self) -> List[Event]:
        """Read-only snapshot of published events."""
        with self._lock:
            return list(self._history)

    def subscribe_wildcard(self, listener: Callable[[Event], None]) -> str:
        """Subscribe to all events.

        Args:
            listener: Callback function

        Returns:
            Subscription ID
        """
        with self._lock:
            self._wildcard_listeners.append(listener)
            self._stats.active_subscriptions = sum(len(v) for v in self._listeners.values()) + len(self._wildcard_listeners)
            return f"sub_wildcard_{id(listener)}"

    def unsubscribe(self, event_type: str, listener: Callable) -> bool:
        """Unsubscribe from event type.

        Args:
            event_type: Event type
            listener: Callback to remove

        Returns:
            True if unsubscribed
        """
        with self._lock:
            if event_type in self._listeners:
                try:
                    self._listeners[event_type].remove(listener)
                    self._stats.active_subscriptions = sum(len(v) for v in self._listeners.values()) + len(self._wildcard_listeners)
                    return True
                except ValueError:
                    pass
            return False

    def unregister(self, event_type: str, listener: Callable) -> bool:
        """Compatibility alias for callers using the registry terminology."""
        if event_type == "*":
            with self._lock:
                try:
                    self._wildcard_listeners.remove(listener)
                    self._stats.active_subscriptions = sum(
                        len(v) for v in self._listeners.values()
                    ) + len(self._wildcard_listeners)
                    return True
                except ValueError:
                    return False
        return self.unsubscribe(event_type, listener)

    def alive(self) -> bool:
        """Return whether the bus is available for publishing."""
        return True

    def add_middleware(self, middleware: Callable[[Event], Optional[Event]]):
        """Add event middleware.

        Args:
            middleware: Function that can modify/drop events
        """
        with self._lock:
            self._middleware.append(middleware)

    def disable_event_type(self, event_type: str):
        """Disable specific event type (will not be published)."""
        with self._lock:
            self._disabled_types.add(event_type)

    def enable_event_type(self, event_type: str):
        """Re-enable disabled event type."""
        with self._lock:
            self._disabled_types.discard(event_type)

    def publish(self, event_type: str, payload: Any = None) -> Optional[Event]:
        """Publish event to all subscribers.

        Args:
            event_type: Type of event
            payload: Event data

        Returns:
            Published Event or None if disabled
        """
        with self._lock:
            if event_type in self._disabled_types:
                return None

            event = Event(event_type=event_type, payload=payload)
            self._history.append(event)
            self._stats.total_published += 1
            self._stats.history_size = len(self._history)

            # Trim history if needed
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history:]

            # Run middleware
            for middleware in self._middleware:
                try:
                    result = middleware(event)
                    if result is None:
                        return None
                    event = result
                except Exception as exc:
                    Logger.warning(f"[EventBus] Middleware error: {exc}")

            # Deliver to specific listeners
            listeners = self._listeners.get(event_type, [])
            for listener in listeners:
                self._deliver(listener, event)

            # Deliver to wildcard listeners
            for listener in self._wildcard_listeners:
                self._deliver(listener, event)

            return event

    def publish_async(self, event_type: str, payload: Any = None) -> asyncio.Task:
        """Publish event asynchronously.

        Returns:
            asyncio.Task for the publish operation
        """
        loop = asyncio.get_event_loop()
        return loop.create_task(self._async_publish(event_type, payload))

    async def _async_publish(self, event_type: str, payload: Any):
        """Async publish implementation."""
        return self.publish(event_type, payload)

    def _deliver(self, listener: Callable, event: Event):
        """Deliver event to listener with error handling."""
        try:
            if asyncio.iscoroutinefunction(listener):
                asyncio.get_event_loop().create_task(listener(event))
            else:
                listener(event)
            self._stats.total_delivered += 1
        except Exception as exc:
            self._stats.total_failed += 1
            Logger.warning(f"[EventBus] Listener error for {event.event_type}: {exc}")

    def get_history(self, event_type: Optional[str] = None, limit: int = 100) -> List[Event]:
        """Get event history.

        Args:
            event_type: Filter by event type
            limit: Maximum events to return

        Returns:
            List of events
        """
        with self._lock:
            events = self._history
            if event_type:
                events = [e for e in events if e.event_type == event_type]
            return events[-limit:]

    def clear_history(self):
        """Clear event history."""
        with self._lock:
            self._history.clear()
            self._stats.history_size = 0

    def get_stats(self) -> EventBusStats:
        """Get event bus statistics."""
        with self._lock:
            return EventBusStats(
                total_published=self._stats.total_published,
                total_delivered=self._stats.total_delivered,
                total_failed=self._stats.total_failed,
                active_subscriptions=self._stats.active_subscriptions,
                history_size=self._stats.history_size,
            )

    def replay(self, event_type: Optional[str] = None, limit: int = 100):
        """Replay events from history.

        Args:
            event_type: Filter by event type
            limit: Maximum events to replay
        """
        events = self.get_history(event_type, limit)
        for event in events:
            try:
                listeners = self._listeners.get(event.event_type, [])
                for listener in listeners:
                    self._deliver(listener, event)
            except Exception:
                pass
