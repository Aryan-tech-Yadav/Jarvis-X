from enum import Enum


class ExecutionState(str, Enum):
    CREATED = "created"
    PLANNING = "planning"
    EXECUTING = "executing"
    TESTING = "testing"
    REPAIRING = "repairing"
    VALIDATING = "validating"
    RELEASING = "releasing"
    FINISHED = "finished"
    FAILED = "failed"
    RECOVERING = "recovering"
    STOPPED = "stopped"


class ExecutionStateMachine:
    """Enforce explicit project lifecycle transitions.

    A state machine is deliberately per execution context, avoiding global
    runtime state leaking between workspace projects.
    """

    TRANSITIONS = {
        ExecutionState.CREATED: {ExecutionState.PLANNING, ExecutionState.RECOVERING, ExecutionState.STOPPED},
        ExecutionState.PLANNING: {ExecutionState.EXECUTING, ExecutionState.TESTING, ExecutionState.VALIDATING,
                                  ExecutionState.FAILED, ExecutionState.STOPPED},
        ExecutionState.EXECUTING: {ExecutionState.TESTING, ExecutionState.REPAIRING, ExecutionState.VALIDATING,
                                   ExecutionState.RELEASING, ExecutionState.FAILED, ExecutionState.STOPPED},
        ExecutionState.TESTING: {ExecutionState.REPAIRING, ExecutionState.VALIDATING, ExecutionState.RELEASING,
                                 ExecutionState.FAILED, ExecutionState.STOPPED},
        ExecutionState.REPAIRING: {ExecutionState.EXECUTING, ExecutionState.TESTING, ExecutionState.VALIDATING,
                                   ExecutionState.FAILED, ExecutionState.STOPPED},
        ExecutionState.VALIDATING: {ExecutionState.REPAIRING, ExecutionState.RELEASING, ExecutionState.FINISHED,
                                    ExecutionState.FAILED, ExecutionState.STOPPED},
        ExecutionState.RELEASING: {ExecutionState.FINISHED, ExecutionState.FAILED, ExecutionState.STOPPED},
        ExecutionState.FAILED: {ExecutionState.RECOVERING, ExecutionState.STOPPED},
        ExecutionState.RECOVERING: {ExecutionState.PLANNING, ExecutionState.EXECUTING, ExecutionState.TESTING,
                                    ExecutionState.REPAIRING, ExecutionState.VALIDATING, ExecutionState.RELEASING,
                                    ExecutionState.FAILED, ExecutionState.STOPPED},
        ExecutionState.FINISHED: {ExecutionState.STOPPED},
        ExecutionState.STOPPED: set(),
    }

    def __init__(self, state=ExecutionState.CREATED):
        self.state = self._coerce(state)
        self.history = [self.state.value]

    def can_transition(self, target):
        return self._coerce(target) in self.TRANSITIONS[self.state]

    def transition(self, target):
        target = self._coerce(target)
        if not self.can_transition(target):
            raise ValueError("Illegal execution state transition: {} -> {}".format(self.state.value, target.value))
        self.state = target
        self.history.append(target.value)
        return self.state

    def restore(self, state):
        """Restore a persisted state only during recovery; it records the action."""
        state = self._coerce(state)
        self.state = state
        self.history.append(state.value)
        return state

    def to_dict(self):
        return {"state": self.state.value, "history": list(self.history)}

    @classmethod
    def from_dict(cls, value):
        machine = cls(value.get("state", ExecutionState.CREATED))
        history = value.get("history")
        if isinstance(history, list) and history:
            machine.history = [str(item) for item in history]
        return machine

    @staticmethod
    def _coerce(value):
        return value if isinstance(value, ExecutionState) else ExecutionState(str(value))
