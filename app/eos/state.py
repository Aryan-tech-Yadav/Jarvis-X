"""EOS state manager."""

from app.eos.state_machine import EOSState, EOSStateMachine


class StateManager(EOSStateMachine):
    pass


__all__ = ["EOSState", "StateManager"]

