from app.workflow.workflow_executor import WorkflowExecutor
from app.workflow.workflow_history import WorkflowHistory
from app.workflow.workflow_registry import WorkflowRegistry


class WorkflowManager:
    """Owns injected handlers and executes a prepared workflow with an isolated run history."""

    def __init__(self, registry=None, event_bus=None):
        self.registry = registry or WorkflowRegistry()
        self.event_bus = event_bus

    def run(self, workflow, context=None):
        history = WorkflowHistory()
        return WorkflowExecutor(self.registry, history, self.event_bus).execute(workflow, context)
