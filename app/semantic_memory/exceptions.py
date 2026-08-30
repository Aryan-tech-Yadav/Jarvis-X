class SemanticMemoryError(Exception):
    """Base exception for semantic-memory failures."""


class SemanticMemoryValidationError(SemanticMemoryError, ValueError):
    """Raised when a semantic-memory value cannot be safely stored."""
