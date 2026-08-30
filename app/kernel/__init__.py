"""Autonomous execution kernel built on Jarvis-X runtime and pipeline contracts.

The kernel is a composition boundary: it coordinates explicitly supplied graph
handlers, checkpoints their serializable state, and never discovers or executes
work implicitly after recovery.
"""

from .boot_manager import KernelBootManager
from .checkpoint_manager import CheckpointManager
from .dispatcher import KernelDispatcher
from .execution_context import ExecutionContext
from .execution_graph import ExecutionGraph
from .execution_history import ExecutionHistory
from .execution_report import ExecutionReport
from .kernel import AutonomousExecutionKernel
from .monitor import KernelMonitor
from .recovery_engine import RecoveryEngine
from .resource_manager import ResourceManager
from .rollback_manager import RollbackManager
from .scheduler import KernelScheduler
from .state_machine import ExecutionState, ExecutionStateMachine
from .watchdog import KernelWatchdog

__all__ = [
    "AutonomousExecutionKernel",
    "ExecutionContext",
    "ExecutionState",
    "ExecutionStateMachine",
    "KernelBootManager",
    "KernelDispatcher",
    "KernelScheduler",
    "KernelMonitor",
    "KernelWatchdog",
    "ExecutionGraph",
    "ExecutionHistory",
    "ExecutionReport",
    "CheckpointManager",
    "RollbackManager",
    "RecoveryEngine",
    "ResourceManager",
]
