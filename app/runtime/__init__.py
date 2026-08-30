"""Runtime package - Jarvis-X Autonomous Runtime Integration.

Components:
  - RuntimeContext: Shared context for all modules
  - ExecutionGraph: DAG-based task orchestration
  - TaskStateMachine: Task lifecycle management
  - ArtifactManager: Project artifact management
  - ReflectionEngine: Post-execution analysis
  - LearningEngine: Learning generation from reflections
  - DashboardBackend: Status.json generation
"""

from app.runtime.runtime_context import RuntimeContext
from app.runtime.execution_graph import ExecutionGraph, ExecutionNode, NodeStatus
from app.runtime.task_state import TaskState, TaskStateTransition
from app.runtime.state_machine import TaskStateMachine, StateChange
from app.runtime.artifact_manager import ArtifactManager
from app.runtime.reflection_engine import ReflectionEngine, ReflectionResult
from app.runtime.learning_engine import LearningEngine, Learning
from app.runtime.dashboard_backend import DashboardBackend
from app.runtime.core_runtime import CoreRuntime

__all__ = [
    "RuntimeContext",
    "ExecutionGraph",
    "ExecutionNode",
    "NodeStatus",
    "TaskState",
    "TaskStateTransition",
    "TaskStateMachine",
    "StateChange",
    "ArtifactManager",
    "ReflectionEngine",
    "ReflectionResult",
    "LearningEngine",
    "Learning",
    "DashboardBackend",
    "CoreRuntime",
]
