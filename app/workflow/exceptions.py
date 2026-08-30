class WorkflowError(Exception):
    """Base exception for workflow failures."""


class WorkflowValidationError(WorkflowError, ValueError):
    """Raised when a workflow has invalid stages or dependencies."""


class WorkflowExecutionError(WorkflowError):
    """Raised when a required workflow handler cannot safely run."""
