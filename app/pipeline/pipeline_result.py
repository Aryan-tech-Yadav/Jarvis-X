from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class PipelineResult:
    success: bool
    status: str
    context: Any
    completed_stages: List[str] = field(default_factory=list)
    failed_stage: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[Any] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def to_dict(self):
        return {
            "success": self.success,
            "status": self.status,
            "context": self.context.as_dict() if hasattr(self.context, "as_dict") else self.context,
            "completed_stages": list(self.completed_stages),
            "failed_stage": self.failed_stage or None,
            "metrics": dict(self.metrics),
            "artifacts": list(self.artifacts),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }
