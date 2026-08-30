"""Voice state manager for conversation state machine.

States:
  IDLE -> WAKING -> LISTENING -> THINKING -> SPEAKING -> LISTENING -> SLEEPING
"""

from __future__ import annotations

from enum import Enum, auto
from typing import Optional, Callable, Dict, Any


class VoiceState(Enum):
    """Conversation states for voice interaction."""
    IDLE = auto()
    WAKING = auto()
    LISTENING = auto()
    THINKING = auto()
    SPEAKING = auto()
    SLEEPING = auto()
    ERROR = auto()


class StateTransition:
    """Represents a state transition."""
    def __init__(self, from_state: VoiceState, to_state: VoiceState, trigger: str, action: Optional[Callable] = None):
        self.from_state = from_state
        self.to_state = to_state
        self.trigger = trigger
        self.action = action


class VoiceStateManager:
    """Manages conversation state machine for voice interactions.

    State transitions:
      IDLE + wake_word -> WAKING
      WAKING + recognized -> LISTENING
      LISTENING + speech_end -> THINKING
      THINKING + response_ready -> SPEAKING
      SPEAKING + finished -> LISTENING
      SPEAKING + interrupted -> LISTENING
      LISTENING + silence -> IDLE
      ANY + sleep -> SLEEPING
      SLEEPING + wake_word -> WAKING
    """

    TRANSITIONS = [
        StateTransition(VoiceState.IDLE, VoiceState.WAKING, "wake_word"),
        StateTransition(VoiceState.WAKING, VoiceState.LISTENING, "recognized"),
        StateTransition(VoiceState.LISTENING, VoiceState.THINKING, "speech_end"),
        StateTransition(VoiceState.THINKING, VoiceState.SPEAKING, "response_ready"),
        StateTransition(VoiceState.SPEAKING, VoiceState.LISTENING, "finished"),
        StateTransition(VoiceState.SPEAKING, VoiceState.LISTENING, "interrupted"),
        StateTransition(VoiceState.LISTENING, VoiceState.IDLE, "silence"),
        StateTransition(VoiceState.IDLE, VoiceState.SLEEPING, "sleep"),
        StateTransition(VoiceState.SLEEPING, VoiceState.WAKING, "wake_word"),
    ]

    def __init__(self):
        self._state = VoiceState.IDLE
        self._listeners: Dict[VoiceState, list] = {}
        self._history: list = []

    @property
    def current_state(self) -> VoiceState:
        return self._state

    def transition(self, trigger: str, context: Dict[str, Any] = None) -> bool:
        """Attempt state transition.

        Args:
            trigger: Event triggering the transition
            context: Optional context data

        Returns:
            True if transition succeeded
        """
        context = context or {}

        for transition in self.TRANSITIONS:
            if transition.from_state == self._state and transition.trigger == trigger:
                old_state = self._state
                self._state = transition.to_state
                self._history.append({
                    "from": old_state.name,
                    "to": self._state.name,
                    "trigger": trigger,
                    "context": context,
                })

                if transition.action:
                    try:
                        transition.action(context)
                    except Exception:
                        pass

                self._notify_listeners(old_state, self._state, trigger)
                return True

        return False

    def force_state(self, state: VoiceState):
        """Force state change without transition rules."""
        old_state = self._state
        self._state = state
        self._history.append({
            "from": old_state.name,
            "to": state.name,
            "trigger": "force",
            "context": {},
        })
        self._notify_listeners(old_state, state, "force")

    def add_listener(self, state: VoiceState, callback: Callable[[VoiceState, VoiceState, str], None]):
        """Add state change listener."""
        if state not in self._listeners:
            self._listeners[state] = []
        self._listeners[state].append(callback)

    def _notify_listeners(self, old_state: VoiceState, new_state: VoiceState, trigger: str):
        """Notify listeners of state change."""
        for listener in self._listeners.get(new_state, []):
            try:
                listener(old_state, new_state, trigger)
            except Exception:
                pass

    def get_state_name(self) -> str:
        """Get current state as string."""
        return self._state.name

    def is_speaking(self) -> bool:
        return self._state == VoiceState.SPEAKING

    def is_listening(self) -> bool:
        return self._state == VoiceState.LISTENING

    def is_idle(self) -> bool:
        return self._state == VoiceState.IDLE

    def is_sleeping(self) -> bool:
        return self._state == VoiceState.SLEEPING
