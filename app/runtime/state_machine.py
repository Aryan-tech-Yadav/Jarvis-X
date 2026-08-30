"""State Machine for task lifecycle management.

Manages task state transitions with validation,
history tracking, and event emission.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field

from app.runtime.task_state import TaskState, TaskStateTransition
from app.core.logger import Logger


@dataclass
class StateChange:
    """Record of a state change."""
    from_state: str
    to_state: str
    timestamp: str
    trigger: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class TaskStateMachine:
    """State machine for task lifecycle management.

    Features:
      - Validated state transitions
      - History tracking
      - Event callbacks
      - Metadata preservation
    """

    def __init__(self, initial_state: TaskState = TaskState.CREATED):
        self._state = initial_state
        self._history: List[StateChange] = []
        self._listeners: Dict[str, List[Callable]] = {}
        self._metadata: Dict[str, Any] = {}

    @property
    def state(self) -> TaskState:
        """Current state."""
        return self._state

    @property
    def state_name(self) -> str:
        """Current state as string."""
        return self._state.value

    @property
    def history(self) -> List[StateChange]:
        """State change history."""
        return list(self._history)

    def can_transition(self, to_state: TaskState) -> bool:
        """Check if transition is valid.

        Args:
            to_state: Target state

        Returns:
            True if transition is allowed
        """
        return TaskStateTransition.is_valid_transition(self._state, to_state)

    def transition(self, to_state: TaskState, trigger: str = "", metadata: Dict[str, Any] = None) -> bool:
        """Attempt state transition.

        Args:
            to_state: Target state
            trigger: Event that triggered transition
            metadata: Additional metadata

        Returns:
            True if transition succeeded
        """
        if not self.can_transition(to_state):
            Logger.warning(f"[StateMachine] Invalid transition: {self._state.value} -> {to_state.value}")
            return False

        old_state = self._state
        self._state = to_state

        change = StateChange(
            from_state=old_state.value,
            to_state=to_state.value,
            timestamp=datetime.now().isoformat(),
            trigger=trigger,
            metadata=metadata or {},
        )
        self._history.append(change)

        if metadata:
            self._metadata.update(metadata)

        Logger.info(f"[StateMachine] {old_state.value} -> {to_state.value} ({trigger})")
        self._notify_listeners(old_state, to_state, trigger)
        return True

    def force_state(self, to_state: TaskState, trigger: str = ""):
        """Force state change without validation.

        Use only for recovery scenarios.

        Args:
            to_state: Target state
            trigger: Event description
        """
        old_state = self._state
        self._state = to_state

        change = StateChange(
            from_state=old_state.value,
            to_state=to_state.value,
            timestamp=datetime.now().isoformat(),
            trigger=f"FORCED: {trigger}",
            metadata={"forced": True},
        )
        self._history.append(change)
        Logger.warning(f"[StateMachine] FORCED: {old_state.value} -> {to_state.value}")

    def reset(self):
        """Reset state machine to initial state."""
        self._state = TaskState.CREATED
        self._history.clear()
        self._metadata.clear()

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value.

        Args:
            key: Metadata key
            default: Default value

        Returns:
            Metadata value
        """
        return self._metadata.get(key, default)

    def set_metadata(self, key: str, value: Any):
        """Set metadata value.

        Args:
            key: Metadata key
            value: Metadata value
        """
        self._metadata[key] = value

    def add_listener(self, event: str, callback: Callable):
        """Add state change listener.

        Args:
            event: Event to listen for (state name or '*')
            callback: Callback function
        """
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(callback)

    def _notify_listeners(self, old_state: TaskState, new_state: TaskState, trigger: str):
        """Notify listeners of state change."""
        for event in [new_state.value, "*"]:
            for listener in self._listeners.get(event, []):
                try:
                    listener(old_state, new_state, trigger)
                except Exception as exc:
                    Logger.warning(f"[StateMachine] Listener error: {exc}")

    def is_terminal(self) -> bool:
        """Check if current state is terminal."""
        return self._state in (TaskState.DONE, TaskState.FAILED, TaskState.CANCELLED)

    def is_active(self) -> bool:
        """Check if task is actively executing."""
        return self._state in (
            TaskState.PLANNED,
            TaskState.RESEARCHING,
            TaskState.CODING,
            TaskState.TESTING,
            TaskState.FIXING,
            TaskState.BENCHMARKING,
            TaskState.REFLECTING,
            TaskState.LEARNING,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert state machine to dictionary."""
        return {
            "current_state": self._state.value,
            "is_terminal": self.is_terminal(),
            "is_active": self.is_active(),
            "history": [
                {
                    "from": h.from_state,
                    "to": h.to_state,
                    "trigger": h.trigger,
                    "timestamp": h.timestamp,
                }
                for h in self._history
            ],
            "metadata": self._metadata,
        }


# Import datetime for timestamps
from datetime import datetime
