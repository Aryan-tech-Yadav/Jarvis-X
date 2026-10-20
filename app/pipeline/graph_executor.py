"""Pipeline graph execution compatibility facade."""

from app.orchestrator.workflow_engine import WorkflowEngine

GraphExecutor = WorkflowEngine

__all__ = ["GraphExecutor", "WorkflowEngine"]
