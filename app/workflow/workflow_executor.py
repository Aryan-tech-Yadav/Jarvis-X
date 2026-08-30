from app.workflow.exceptions import WorkflowExecutionError
from app.workflow.models import WorkflowStatus, WorkflowStepStatus
from app.workflow.workflow_context import WorkflowContext


class WorkflowExecutor:
    """Runs only injected handlers and never grants filesystem or tool permissions itself."""

    def __init__(self, registry, history=None, event_bus=None):
        self.registry = registry
        self.history = history
        self.event_bus = event_bus

    def execute(self, workflow, context=None):
        run_context = WorkflowContext(workflow.goal, context)
        workflow.status = WorkflowStatus.RUNNING
        self._record("workflow_started", details={"workflow_id": workflow.workflow_id})
        while True:
            ready = [step for step in workflow.steps if self._ready(step, workflow, run_context)]
            if not ready:
                break
            for step in ready:
                if step.when and not run_context.has_signal(step.when):
                    step.status = WorkflowStepStatus.SKIPPED
                    self._record("step_skipped", step.step_id, {"when": step.when})
                    continue
                self._run_step(step, run_context)
                if step.status == WorkflowStepStatus.FAILED:
                    workflow.status = WorkflowStatus.FAILED
                    self._record("workflow_failed", step.step_id)
                    return self._result(workflow, run_context)
        unfinished = [step for step in workflow.steps if step.status == WorkflowStepStatus.PENDING]
        workflow.status = WorkflowStatus.COMPLETED if not unfinished else WorkflowStatus.FAILED
        self._record("workflow_completed" if not unfinished else "workflow_blocked", details={"pending": [step.step_id for step in unfinished]})
        return self._result(workflow, run_context)

    def _ready(self, step, workflow, context):
        if step.status != WorkflowStepStatus.PENDING:
            return False
        dependencies = [workflow.step(identifier) for identifier in step.depends_on]
        return all(dependency and dependency.status in {WorkflowStepStatus.COMPLETED, WorkflowStepStatus.SKIPPED}
                   for dependency in dependencies)

    def _run_step(self, step, context):
        handler = self.registry.get(step.step_id)
        if handler is None:
            if step.required:
                step.status = WorkflowStepStatus.FAILED
                self._record("step_failed", step.step_id, {"error": "No handler registered"})
                return
            step.status = WorkflowStepStatus.SKIPPED
            self._record("step_skipped", step.step_id, {"reason": "No optional handler registered"})
            return
        step.status = WorkflowStepStatus.RUNNING
        self._record("step_started", step.step_id)
        try:
            result = handler(step, context.to_dict())
        except Exception as error:
            result = {"success": False, "error": str(error)}
        if not isinstance(result, dict):
            result = {"success": False, "error": "Handler must return a dictionary"}
        context.record(step.step_id, result)
        if result.get("success") is True:
            step.status = WorkflowStepStatus.COMPLETED
            self._record("step_completed", step.step_id, result)
        else:
            step.status = WorkflowStepStatus.FAILED
            self._record("step_failed", step.step_id, result)

    def _record(self, event, step_id=None, details=None):
        if self.history:
            self.history.record(event, step_id, details)
        if self.event_bus:
            self.event_bus.publish(f"WORKFLOW_{event.upper()}", {"step_id": step_id, **(details or {})})

    def _result(self, workflow, context):
        return {
            "success": workflow.status == WorkflowStatus.COMPLETED,
            "workflow": workflow.to_dict(),
            "context": context.to_dict(),
            "history": self.history.events() if self.history else [],
        }
