"""Stable result contract for cross-module engineering workflows."""

from dataclasses import dataclass, field
from time import perf_counter
from typing import Any, Dict, Iterable, List, Optional


@dataclass
class ExecutionResult:
    """Normalized outcome that can cross module and UI boundaries safely."""

    success: bool
    status: str
    message: str = ""
    data: Any = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    artifacts: List[Any] = field(default_factory=list)
    duration: float = 0.0

    def __post_init__(self):
        self.success = bool(self.success)
        self.status = str(self.status or ("completed" if self.success else "failed"))
        self.message = str(self.message or "")
        self.metrics = dict(self.metrics or {})
        self.warnings = self._strings(self.warnings)
        self.errors = self._strings(self.errors)
        self.artifacts = list(self.artifacts or [])
        self.duration = max(0.0, float(self.duration or 0.0))
        if self.success and self.status == "failed":
            raise ValueError("A successful result cannot have failed status")
        if not self.success and not self.errors and self.message:
            self.errors.append(self.message)

    @classmethod
    def completed(cls, data=None, message="Completed", *, metrics=None, warnings=None, artifacts=None, duration=0.0):
        return cls(True, "completed", message, data if data is not None else {}, metrics or {}, warnings or [], [], artifacts or [], duration)

    @classmethod
    def failed(cls, message, *, data=None, errors=None, metrics=None, warnings=None, artifacts=None, duration=0.0, status="failed"):
        error_list = list(errors or [])
        if not error_list and message:
            error_list.append(str(message))
        return cls(False, status, str(message), data if data is not None else {}, metrics or {}, warnings or [], error_list, artifacts or [], duration)

    @classmethod
    def from_legacy(cls, value, *, message=None, duration=0.0):
        """Adapt the existing dictionary/bool/tuple result patterns."""
        if isinstance(value, cls):
            return value
        if isinstance(value, dict):
            success = bool(value.get("success", not bool(value.get("error"))))
            output = value.get("data", value)
            resolved_message = message or value.get("message") or value.get("error") or ("Completed" if success else "Operation failed")
            warnings = value.get("warnings", [])
            errors = value.get("errors", [])
            if value.get("error"):
                errors = [*errors, value["error"]]
            artifacts = value.get("artifacts", [])
            metrics = value.get("metrics", {})
            return cls(success, value.get("status", "completed" if success else "failed"), resolved_message, output, metrics, warnings, errors, artifacts, duration)
        if isinstance(value, tuple) and len(value) == 2 and isinstance(value[0], bool):
            success, output = value
            return cls.completed(output, message or "Completed", duration=duration) if success else cls.failed(str(output), data=output, duration=duration)
        if isinstance(value, bool):
            return cls.completed(message=message or "Completed", duration=duration) if value else cls.failed(message or "Operation failed", duration=duration)
        return cls.completed(value, message or "Completed", duration=duration)

    def to_dict(self):
        return {
            "success": self.success,
            "status": self.status,
            "message": self.message,
            "data": self.data,
            "metrics": dict(self.metrics),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "artifacts": list(self.artifacts),
            "duration": self.duration,
        }

    @staticmethod
    def timed(callable_, *args, **kwargs):
        started = perf_counter()
        try:
            return ExecutionResult.from_legacy(callable_(*args, **kwargs), duration=perf_counter() - started)
        except Exception as error:
            return ExecutionResult.failed(str(error), duration=perf_counter() - started)

    @staticmethod
    def _strings(values: Optional[Iterable[Any]]):
        if values is None:
            return []
        if isinstance(values, str):
            return [values] if values else []
        return [str(value) for value in values if str(value)]
