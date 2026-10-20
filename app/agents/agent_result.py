from dataclasses import dataclass, field
from typing import Any, List


@dataclass
class AgentResult:
    success: bool
    summary: str = ""
    files: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    duration: float = 0.0

    def to_dict(self):
        return {"success": self.success, "summary": self.summary, "files": self.files,
                "warnings": self.warnings, "errors": self.errors, "duration": self.duration}