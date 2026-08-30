"""Task State definitions and transitions.

Task lifecycle:
  CREATED -> PLANNED -> RESEARCHING -> CODING -> TESTING -> FIXING -> BENCHMARKING -> DONE
                                                                    |
                                                                    v
                                                                  FAILED
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional


class TaskState(str, Enum):
    """Task execution states."""
    CREATED = "created"
    PLANNED = "planned"
    RESEARCHING = "researching"
    CODING = "coding"
    TESTING = "testing"
    FIXING = "fixing"
    BENCHMARKING = "benchmarking"
    REFLECTING = "reflecting"
    LEARNING = "learning"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStateTransition:
    """Defines a valid state transition."""

    TRANSITIONS = {
        TaskState.CREATED: [TaskState.PLANNED, TaskState.CANCELLED],
        TaskState.PLANNED: [TaskState.RESEARCHING, TaskState.CODING, TaskState.TESTING, TaskState.DONE, TaskState.FAILED],
        TaskState.RESEARCHING: [TaskState.CODING, TaskState.PLANNED, TaskState.FAILED],
        TaskState.CODING: [TaskState.TESTING, TaskState.FIXING, TaskState.BENCHMARKING, TaskState.FAILED],
        TaskState.TESTING: [TaskState.FIXING, TaskState.BENCHMARKING, TaskState.DONE, TaskState.FAILED],
        TaskState.FIXING: [
            TaskState.TESTING,
            TaskState.CODING,
            TaskState.BENCHMARKING,
            TaskState.FAILED,
        ],
        TaskState.BENCHMARKING: [TaskState.REFLECTING, TaskState.DONE, TaskState.FAILED],
        TaskState.REFLECTING: [TaskState.LEARNING, TaskState.DONE, TaskState.FAILED],
        TaskState.LEARNING: [TaskState.DONE, TaskState.FAILED],
    }

    @classmethod
    def is_valid_transition(cls, from_state: TaskState, to_state: TaskState) -> bool:
        """Check if transition is valid.

        Args:
            from_state: Current state
            to_state: Target state

        Returns:
            True if transition is valid
        """
        allowed = cls.TRANSITIONS.get(from_state, [])
        return to_state in allowed

    @classmethod
    def get_allowed_transitions(cls, from_state: TaskState) -> List[TaskState]:
        """Get all allowed transitions from a state.

        Args:
            from_state: Current state

        Returns:
            List of allowed target states
        """
        return cls.TRANSITIONS.get(from_state, [])
