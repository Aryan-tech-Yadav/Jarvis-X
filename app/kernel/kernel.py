"""Autonomous Execution Kernel coordination boundary."""

from typing import Any, Dict, Optional

from app.core.results import ExecutionResult
from .boot_manager import KernelBootManager
from .checkpoint_manager import CheckpointManager
from .dispatcher import KernelDispatcher
from .execution_context import ExecutionContext
from .execution_graph import ExecutionGraph
from .execution_history import ExecutionHistory
from .execution_report import ExecutionReport
from .recovery_engine import RecoveryEngine
from .resource_manager import ResourceManager
from .rollback_manager import RollbackManager
from .scheduler import KernelScheduler
from .state_machine import ExecutionState, ExecutionStateMachine


class AutonomousExecutionKernel:
    """Coordinates explicit handlers, graph scheduling, checkpoints, and recovery."""

    def __init__(
        self,
        checkpoint_dir: Optional[str] = None,
        max_parallel: int = 1,
        default_retries: int = 0,
        resource_manager: Optional[ResourceManager] = None,
    ):
        self.resource_manager = resource_manager or ResourceManager()
        self.dispatcher = KernelDispatcher()
        self.history = ExecutionHistory()
        self.reporter = ExecutionReport()
        self.checkpoint_manager = CheckpointManager(checkpoint_dir) if checkpoint_dir else None
        self.rollback_manager = RollbackManager(self.checkpoint_manager) if self.checkpoint_manager else None
        self.recovery_engine = RecoveryEngine(self.checkpoint_manager, self.rollback_manager) if self.checkpoint_manager else None
        self.max_parallel = max_parallel
        self.default_retries = default_retries
        self.boot_manager = KernelBootManager()

    def register_handler(self, node_id: str, handler):
        return self.dispatcher.register(node_id, handler)

    def execute(self, graph: ExecutionGraph, context: ExecutionContext) -> ExecutionResult:
        scheduler = KernelScheduler(
            graph,
            resource_manager=self.resource_manager,
            max_parallel=self.max_parallel,
            default_retries=self.default_retries,
        )
        context.state_machine.transition(ExecutionState.RUNNING)
        context.record("KERNEL_EXECUTION_STARTED", {"goal": context.goal, "nodes": list(graph.nodes.keys())})

        while not graph.is_completed(context.completed_nodes):
            batch = scheduler.next_batch(context)
            nodes = batch.get("nodes", [])
            if not nodes:
                if batch.get("paused"):
                    context.state_machine.transition(ExecutionState.SUSPENDED)
                    return ExecutionResult.failed("Kernel paused due to resource admission or delay", data=self.reporter.build(context, graph=graph))
                unresolved = [k for k in graph.nodes if k not in context.completed_nodes]
                context.state_machine.transition(ExecutionState.FAILED)
                return ExecutionResult.failed(f"Kernel deadlock or missing dependencies for nodes: {unresolved}", data=self.reporter.build(context, graph=graph))

            for node in nodes:
                node_id = node["id"]
                context.mark_started(node_id)
                res = self.dispatcher.dispatch(node, context)
                if res.success:
                    context.mark_completed(node_id, result=res.data)
                    self.history.record(
                        "NODE_COMPLETED",
                        run_id=context.run_id,
                        node_id=node_id,
                        payload={"success": True, "data": res.data},
                    )
                    if self.checkpoint_manager:
                        self.checkpoint_manager.create(node_id, {"context": context.to_dict(), "graph": graph.to_dict()})
                else:
                    context.mark_failed(node_id, error=res.message)
                    self.history.record(
                        "NODE_FAILED",
                        run_id=context.run_id,
                        node_id=node_id,
                        payload={"success": False, "message": res.message},
                    )
                    can_retry = scheduler.retry_or_fail(context, node)
                    if not can_retry:
                        context.state_machine.transition(ExecutionState.FAILED)
                        return ExecutionResult.failed(f"Node {node_id} failed: {res.message}", data=self.reporter.build(context, graph=graph))

        context.state_machine.transition(ExecutionState.COMPLETED)
        report = self.reporter.build(context, graph=graph)
        return ExecutionResult.completed(data=report, message="Kernel execution finished successfully")
