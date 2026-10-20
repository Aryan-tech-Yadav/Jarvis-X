from enum import Enum
from typing import Callable, List


class EOSState(str, Enum):
    IDLE = "idle"
    UNDERSTANDING = "understanding"
    PLANNING = "planning"
    RESEARCH = "research"
    CODING = "coding"
    TESTING = "testing"
    REPAIR = "repair"
    VALIDATION = "validation"
    DOCUMENTATION = "documentation"
    DEPLOYMENT = "deployment"
    COMPLETED = "completed"
    FAILED = "failed"


class EOSStateMachine:
    def __init__(self):
        self.state = EOSState.IDLE
        self.history: List[dict] = []
        self._listeners: List[Callable[[EOSState, EOSState], None]] = []

    def add_listener(self, listener: Callable[[EOSState, EOSState], None]) -> None:
        self._listeners.append(listener)

    def transition(self, state: EOSState, trigger: str = "") -> None:
        previous = self.state
        self.state = EOSState(state)
        self.history.append({"from": previous.value, "to": self.state.value, "trigger": trigger})
        for listener in self._listeners:
            listener(previous, self.state)
