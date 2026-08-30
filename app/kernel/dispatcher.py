from inspect import signature
from time import perf_counter

from app.core.results import ExecutionResult


class KernelDispatcher:
    """Explicit handler registry; nodes cannot execute without a registered handler."""

    def __init__(self):
        self._handlers = {}

    def register(self, node_id, handler):
        if not callable(handler):
            raise TypeError("Kernel node handler must be callable")
        node_id = str(node_id)
        if not node_id:
            raise ValueError("Kernel node identifier cannot be empty")
        self._handlers[node_id] = handler
        return handler

    def dispatch(self, node, context):
        node_id = self._node_id(node)
        handler = self._handlers.get(node_id)
        if handler is None:
            return ExecutionResult.failed("No handler registered for kernel node: " + node_id, status="unavailable")
        started = perf_counter()
        try:
            result = self._normalize(self._invoke(handler, context, node))
        except Exception as error:
            result = ExecutionResult.failed(str(error))
        result.duration = max(result.duration, perf_counter() - started)
        return result

    @staticmethod
    def _invoke(handler, context, node):
        parameters = signature(handler).parameters
        return handler(context, node) if len(parameters) >= 2 else handler(context)

    @staticmethod
    def _normalize(value):
        if isinstance(value, ExecutionResult):
            return value
        if hasattr(value, "success") and hasattr(value, "status"):
            data = value.to_dict() if hasattr(value, "to_dict") else value
            return ExecutionResult(bool(value.success), str(value.status), getattr(value, "message", ""), data)
        return ExecutionResult.from_legacy(value)

    @staticmethod
    def _node_id(node):
        if isinstance(node, dict):
            return str(node.get("id") or node.get("node_id") or "")
        return str(getattr(node, "node_id", getattr(node, "id", "")))
