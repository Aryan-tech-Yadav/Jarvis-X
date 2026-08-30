from abc import ABC, abstractmethod

from app.core.results import ExecutionResult


class PipelineStage(ABC):
    """Contract for a generation stage; stages may not mutate global state."""

    @property
    @abstractmethod
    def name(self):
        """Stable stage identifier used for resume, events, and reports."""

    def validate(self, context):
        return ExecutionResult.completed(message="Stage input validated")

    @abstractmethod
    def execute(self, context):
        """Return an ExecutionResult or a value supported by that contract."""

    def rollback(self, context):
        return ExecutionResult.completed(message="No rollback action required")

    def metrics(self):
        return {}
