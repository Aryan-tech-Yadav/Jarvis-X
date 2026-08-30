"""Event subscribers registry.

Manages subscriptions with automatic cleanup,
lifecycle hooks, and dependency tracking.
"""

from __future__ import annotations

import threading
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass, field

from app.events.event import Event
from app.events.event_bus import EventBus
from app.core.logger import Logger


@dataclass
class Subscription:
    """Event subscription record."""
    subscription_id: str
    event_type: str
    listener: Callable
    is_wildcard: bool = False
    is_async: bool = False
    created_at: str = ""
    call_count: int = 0
    last_called: str = ""


class SubscriberRegistry:
    """Registry for event subscribers with lifecycle management.

    Features:
      - Subscription tracking
      - Automatic cleanup
      - Dependency tracking
      - Subscription groups
    """

    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus
        self._subscriptions: Dict[str, Subscription] = {}
        self._groups: Dict[str, List[str]] = {}
        self._lock = threading.RLock()
        self._counter = 0

    def register(self, event_type: str, listener: Callable[[Event], None], group: str = "default") -> str:
        """Register a subscriber.

        Args:
            event_type: Event type to subscribe to
            listener: Callback function
            group: Subscription group for bulk management

        Returns:
            Subscription ID
        """
        with self._lock:
            self._counter += 1
            sub_id = f"sub_{self._counter}_{event_type}"

            is_async = False
            try:
                import asyncio
                is_async = asyncio.iscoroutinefunction(listener)
            except Exception:
                pass

            subscription = Subscription(
                subscription_id=sub_id,
                event_type=event_type,
                listener=listener,
                is_wildcard=(event_type == "*"),
                is_async=is_async,
            )

            self._subscriptions[sub_id] = subscription

            if group not in self._groups:
                self._groups[group] = []
            self._groups[group].append(sub_id)

            # Subscribe to event bus
            if self.event_bus:
                if event_type == "*":
                    self.event_bus.subscribe_wildcard(listener)
                else:
                    self.event_bus.subscribe(event_type, listener)

            Logger.info(f"[SubscriberRegistry] Registered {sub_id} for {event_type}")
            return sub_id

    def unregister(self, subscription_id: str) -> bool:
        """Unregister a subscriber.

        Args:
            subscription_id: Subscription ID to remove

        Returns:
            True if unregistered
        """
        with self._lock:
            subscription = self._subscriptions.get(subscription_id)
            if not subscription:
                return False

            # Unsubscribe from event bus
            if self.event_bus:
                self.event_bus.unregister(subscription.event_type, subscription.listener)

            # Remove from groups
            for group_ids in self._groups.values():
                if subscription_id in group_ids:
                    group_ids.remove(subscription_id)

            del self._subscriptions[subscription_id]
            Logger.info(f"[SubscriberRegistry] Unregistered {subscription_id}")
            return True

    def unregister_group(self, group: str):
        """Unregister all subscribers in a group.

        Args:
            group: Group name
        """
        with self._lock:
            sub_ids = self._groups.get(group, [])
            for sub_id in list(sub_ids):
                self.unregister(sub_id)
            self._groups.pop(group, None)

    def get_subscription(self, subscription_id: str) -> Optional[Subscription]:
        """Get subscription by ID."""
        with self._lock:
            return self._subscriptions.get(subscription_id)

    def get_group_subscriptions(self, group: str) -> List[Subscription]:
        """Get all subscriptions in a group."""
        with self._lock:
            sub_ids = self._groups.get(group, [])
            return [self._subscriptions[sub_id] for sub_id in sub_ids if sub_id in self._subscriptions]

    def get_all_subscriptions(self) -> List[Subscription]:
        """Get all subscriptions."""
        with self._lock:
            return list(self._subscriptions.values())

    def clear(self):
        """Clear all subscriptions."""
        with self._lock:
            for sub_id in list(self._subscriptions.keys()):
                self.unregister(sub_id)
            self._groups.clear()
            self._counter = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        with self._lock:
            return {
                "total_subscriptions": len(self._subscriptions),
                "total_groups": len(self._groups),
                "async_subscriptions": sum(1 for s in self._subscriptions.values() if s.is_async),
                "wildcard_subscriptions": sum(1 for s in self._subscriptions.values() if s.is_wildcard),
            }
