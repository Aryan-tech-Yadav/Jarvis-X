from app.workflow.workflow_builder import WorkflowBuilder
from app.workflow.workflow_manager import WorkflowManager


class WorkflowEngine:
    """Public API for selecting a workflow and, when handlers are supplied, running it."""

    def __init__(self, builder=None, manager=None):
        self.builder = builder or WorkflowBuilder()
        self.manager = manager or WorkflowManager()

    def prepare(self, goal, requirements=None, risk=None, simulation=None):
        return self.builder.build(goal, requirements, risk, simulation)

    def run(self, workflow, context=None):
        return self.manager.run(workflow, context)
