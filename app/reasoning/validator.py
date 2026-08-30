"""Validation contract for plans and execution results."""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ValidationReport:
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"valid": self.valid, "errors": list(self.errors), "warnings": list(self.warnings)}


class Validator:
    def validate(self, value: Any) -> ValidationReport:
        if value is None:
            return ValidationReport(False, errors=["Result cannot be None"])
        if isinstance(value, dict) and value.get("success") is False:
            return ValidationReport(False, errors=[str(value.get("error") or "Execution failed")])
        return ValidationReport(True)

