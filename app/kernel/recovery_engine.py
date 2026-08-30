from app.core.results import ExecutionResult

from .execution_context import ExecutionContext
from .state_machine import ExecutionState


class RecoveryEngine:
    """Restores serialized state only; re-dispatch always requires explicit handlers."""

    def __init__(self, checkpoints, rollback_manager=None):
        self.checkpoints = checkpoints
        self.rollback_manager = rollback_manager

    def recover(self, checkpoint_id=None):
        record = self._record(checkpoint_id)
        if record is None:
            return ExecutionResult.failed("No checkpoint is available for recovery", status="unavailable")
        payload = record.get("payload", {})
        try:
            context = ExecutionContext.from_dict(payload["context"])
            context.state_machine.restore(ExecutionState.RECOVERING)
            context.record("KERNEL_RECOVERED", {"checkpoint_id": record["id"], "stage": record.get("stage")})
            return ExecutionResult.completed({"context": context, "graph": payload.get("graph", {}), "checkpoint": record},
                                             "Kernel state restored; explicitly resume with bound handlers")
        except (KeyError, TypeError, ValueError) as error:
            return ExecutionResult.failed("Invalid checkpoint: " + str(error))

    def _record(self, checkpoint_id):
        if self.rollback_manager is not None:
            return self.rollback_manager.rollback(checkpoint_id)
        return self.checkpoints.load(checkpoint_id) if checkpoint_id else self.checkpoints.latest()
