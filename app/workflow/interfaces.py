from typing import Any, Dict, Protocol

from app.workflow.models import WorkflowStep


class WorkflowHandler(Protocol):
    def __call__(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Return at least a success boolean; optionally return context updates."""
