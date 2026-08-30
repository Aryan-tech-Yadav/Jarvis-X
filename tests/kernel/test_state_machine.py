"""Unit tests for Kernel State Machine."""

import unittest

from app.kernel.state_machine import ExecutionState, ExecutionStateMachine


class TestKernelStateMachine(unittest.TestCase):
    def test_valid_transitions(self):
        sm = ExecutionStateMachine()
        self.assertEqual(sm.state, ExecutionState.INITIALIZING)

        sm.transition(ExecutionState.READY)
        self.assertEqual(sm.state, ExecutionState.READY)

        sm.transition(ExecutionState.PLANNING)
        sm.transition(ExecutionState.RUNNING)
        sm.transition(ExecutionState.VALIDATING)
        sm.transition(ExecutionState.COMPLETED)
        self.assertEqual(sm.state, ExecutionState.COMPLETED)

    def test_invalid_transition_raises(self):
        sm = ExecutionStateMachine()
        with self.assertRaises(ValueError):
            sm.transition(ExecutionState.COMPLETED)
