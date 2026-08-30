"""Canonical shared execution context for collaborating agents."""

from app.orchestrator.shared_context import SharedContext

ExecutionContext = SharedContext

__all__ = ["ExecutionContext", "SharedContext"]
