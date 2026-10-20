from dataclasses import dataclass
from typing import Any
from datetime import datetime, timezone


@dataclass
class Observation:
    success: bool
    output: Any = None
    error: str | None = None
    tool: str = ""
    action: str = ""
    step: int = 1
    request: str = ""
    duration: float = 0.0
    changed_files: list = None
    validation: Any = None
    warnings: list = None
    timestamp: str = ""

    def __post_init__(self):
        if self.changed_files is None:
            self.changed_files = []
        if self.warnings is None:
            self.warnings = []
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self):
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "tool": self.tool,
            "action": self.action,
            "step": self.step,
            "request": self.request,
            "duration": self.duration,
            "changed_files": self.changed_files,
            "validation": self.validation,
            "warnings": self.warnings,
            "timestamp": self.timestamp,
        }

    def __getitem__(self, key):
        return self.to_dict()[key]

    def get(self, key, default=None):
        return self.to_dict().get(key, default)
