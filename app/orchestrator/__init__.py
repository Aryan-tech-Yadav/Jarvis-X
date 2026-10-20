from app.orchestrator.orchestrator import OrchestratorResult
from app.orchestrator.scheduler import ExecutionSchedule, TaskScheduler
from app.orchestrator.shared_context import SharedContext
from app.orchestrator.task import Task
from app.orchestrator.task_graph import TaskGraph, TaskNode
from app.orchestrator.task_replay import TaskReplay
from app.orchestrator.agent_context import AgentContext
from app.orchestrator.message_bus import AgentMessage, MessageBus
from app.orchestrator.execution_context import ExecutionContext
from app.orchestrator.workflow_engine import WorkflowEngine

__all__ = [
    "AgentContext",
    "AgentOrchestrator",
    "ExecutionSchedule",
    "MultiAgentOrchestrator",
    "OrchestratorResult",
    "SharedContext",
    "Task",
    "TaskGraph",
    "TaskNode",
    "TaskReplay",
    "TaskScheduler",
    "AgentMessage",
    "MessageBus",
    "ExecutionContext",
    "WorkflowEngine",
]


def __getattr__(name):
    """Load agent orchestrators lazily to keep package imports acyclic."""
    if name == "AgentOrchestrator":
        from app.orchestrator.agent_orchestrator import AgentOrchestrator
        return AgentOrchestrator
    if name == "MultiAgentOrchestrator":
        from app.orchestrator.multi_agent_orchestrator import MultiAgentOrchestrator
        return MultiAgentOrchestrator
    raise AttributeError(name)
