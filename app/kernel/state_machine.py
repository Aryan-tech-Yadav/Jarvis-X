"""Execution lifecycle state machine with backward-compatible state names."""

from enum import Enum


class ExecutionState(str, Enum):
    CREATED = "created"
    INITIALIZING = "created"  # Legacy alias
    READY = "ready"

    PLANNING = "planning"
    EXECUTING = "executing"
    RUNNING = "executing"  # Legacy alias

    TESTING = "testing"
    REPAIRING = "repairing"
    VALIDATING = "validating"
    RELEASING = "releasing"

    FINISHED = "finished"
    COMPLETED = "finished"  # Legacy alias

    FAILED = "failed"
    RECOVERING = "recovering"
    SUSPENDED = "suspended"
    STOPPED = "stopped"


class ExecutionStateMachine:
    """Enforce valid lifecycle transitions for an individual execution."""

    TRANSITIONS = {
        ExecutionState.CREATED: {
            ExecutionState.READY,
            ExecutionState.PLANNING,
            ExecutionState.EXECUTING,
            ExecutionState.RECOVERING,
            ExecutionState.STOPPED,
        },
        ExecutionState.READY: {
            ExecutionState.PLANNING,
            ExecutionState.FAILED,
            ExecutionState.STOPPED,
        },
        ExecutionState.PLANNING: {
            ExecutionState.EXECUTING,
            ExecutionState.TESTING,
            ExecutionState.VALIDATING,
            ExecutionState.FAILED,
            ExecutionState.STOPPED,
        },
        ExecutionState.EXECUTING: {
            ExecutionState.TESTING,
            ExecutionState.REPAIRING,
            ExecutionState.VALIDATING,
            ExecutionState.RELEASING,
            ExecutionState.FINISHED,
            ExecutionState.SUSPENDED,
            ExecutionState.FAILED,
            ExecutionState.STOPPED,
        },
        ExecutionState.TESTING: {
            ExecutionState.REPAIRING,
            ExecutionState.VALIDATING,
            ExecutionState.RELEASING,
            ExecutionState.FAILED,
            ExecutionState.STOPPED,
        },
        ExecutionState.REPAIRING: {
            ExecutionState.EXECUTING,
            ExecutionState.TESTING,
            ExecutionState.VALIDATING,
            ExecutionState.FAILED,
            ExecutionState.STOPPED,
        },
        ExecutionState.VALIDATING: {
            ExecutionState.REPAIRING,
            ExecutionState.RELEASING,
            ExecutionState.FINISHED,
            ExecutionState.FAILED,
            ExecutionState.STOPPED,
        },
        ExecutionState.RELEASING: {
            ExecutionState.FINISHED,
            ExecutionState.FAILED,
            ExecutionState.STOPPED,
        },
        ExecutionState.FAILED: {
            ExecutionState.RECOVERING,
            ExecutionState.STOPPED,
        },
        ExecutionState.RECOVERING: {
            ExecutionState.PLANNING,
            ExecutionState.EXECUTING,
            ExecutionState.TESTING,
            ExecutionState.REPAIRING,
            ExecutionState.VALIDATING,
            ExecutionState.RELEASING,
            ExecutionState.FAILED,
            ExecutionState.STOPPED,
        },
        ExecutionState.SUSPENDED: {
            ExecutionState.EXECUTING,
            ExecutionState.RECOVERING,
            ExecutionState.FAILED,
            ExecutionState.STOPPED,
        },
        ExecutionState.FINISHED: {
            ExecutionState.STOPPED,
        },
        ExecutionState.STOPPED: set(),
    }

    _LEGACY_VALUES = {
        "initializing": ExecutionState.CREATED,
        "running": ExecutionState.EXECUTING,
        "completed": ExecutionState.FINISHED,
    }

    def __init__(self, state=ExecutionState.CREATED):
        self.state = self._coerce(state)
        self.history = [self.state.value]

    def can_transition(self, target):
        target = self._coerce(target)
        return target in self.TRANSITIONS[self.state]

    def transition(self, target):
        target = self._coerce(target)

        if not self.can_transition(target):
            raise ValueError(
                "Illegal execution state transition: "
                f"{self.state.value} -> {target.value}"
            )

        self.state = target
        self.history.append(target.value)
        return self.state

    def restore(self, state):
        """Restore a persisted state and record the restoration."""
        self.state = self._coerce(state)
        self.history.append(self.state.value)
        return self.state

    def to_dict(self):
        return {
            "state": self.state.value,
            "history": list(self.history),
        }

    @classmethod
    def from_dict(cls, value):
        if not isinstance(value, dict):
            raise TypeError("State machine payload must be a dictionary")

        machine = cls(value.get("state", ExecutionState.CREATED))
        history = value.get("history")

        if isinstance(history, list) and history:
            machine.history = [str(item) for item in history]

        return machine

    @classmethod
    def _coerce(cls, value):
        if isinstance(value, ExecutionState):
            return value

        normalized = str(value).strip().lower()

        if normalized in cls._LEGACY_VALUES:
            return cls._LEGACY_VALUES[normalized]

        try:
            return ExecutionState(normalized)
        except ValueError:
            # Also accept enum member names such as "RUNNING".
            try:
                return ExecutionState[normalized.upper()]
            except KeyError:
                raise ValueError(
                    f"Unknown execution state: {value!r}"
                ) from None
